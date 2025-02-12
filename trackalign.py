import os
import sys
import gc
import argparse
import logging
from pydub import AudioSegment
from audalign import (
    FingerprintRecognizer,
    CorrelationRecognizer,
    CorrelationSpectrogramRecognizer,
    VisualRecognizer,
    align_files
)

# Constants for alignment algorithms
ALGORITHMS = {
    'fingerprint': FingerprintRecognizer,
    'correlation': CorrelationRecognizer,
    'correlation_spectrogram': CorrelationSpectrogramRecognizer,
    'visual': VisualRecognizer
}
DEFAULT_ALGORITHM = 'fingerprint'

class LoggerWriter:
    """Redirects stdout/stderr to logging system with timestamps"""
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message.strip():
            logging.log(self.level, message.strip())

    def flush(self):
        pass

def configure_logging(destination_dir):
    """Set up logging to both console and file with timestamps"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter with timestamps
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler (log to destination directory)
    log_file = os.path.join(destination_dir, 'alignment.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Redirect standard streams
    sys.stdout = LoggerWriter(logging.INFO)
    sys.stderr = LoggerWriter(logging.ERROR)

    logging.info(f"Logging system initialized. Full log at {log_file}")

def get_recognizer(algorithm, accuracy=3):
    """Get the appropriate recognizer based on algorithm choice with default settings"""
    if algorithm not in ALGORITHMS:
        logging.warning(f"Unknown algorithm '{algorithm}', using default: {DEFAULT_ALGORITHM}")
        algorithm = DEFAULT_ALGORITHM

    recognizer = ALGORITHMS[algorithm]()

    # Configure common settings
    recognizer.config.freq_threshold = 100
    recognizer.config.multiprocessing = True
    recognizer.config.num_processors = 6

    # Configure algorithm-specific settings
    if algorithm == 'fingerprint':
        recognizer.config.set_accuracy(accuracy)
        recognizer.config.set_hash_style('panako_mod')
    elif algorithm == 'visual':
        recognizer.config.volume_threshold = 215
        recognizer.config.img_width = 0.5

    return recognizer

def list_root_wav_files(directory):
    """List all .wav files in directory root"""
    try:
        return [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(".wav")
        ]
    except Exception as e:
        logging.error(f"File listing error: {e}")
        return []

def split_stereo_to_mono(input_file, temp_dir):
    """Split stereo file to mono channels with existing file check"""
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        left_output = os.path.join(temp_dir, f"{base_name}_L.wav")
        right_output = os.path.join(temp_dir, f"{base_name}_R.wav")

        # Check if files already exist
        if os.path.exists(left_output) and os.path.exists(right_output):
            logging.info(f"Using existing split files for '{input_file}':")
            logging.info(f" - Left channel: '{left_output}'")
            logging.info(f" - Right channel: '{right_output}'")
            return left_output, right_output

        audio = AudioSegment.from_file(input_file)
        channels = audio.channels

        if channels == 1:
            # If mono, check if temp file exists
            mono_output = os.path.join(temp_dir, os.path.basename(input_file))
            if os.path.exists(mono_output):
                logging.info(f"Using existing mono file: {mono_output}")
                return mono_output, None

            # If not exists, create it
            audio.export(mono_output, format="wav")
            logging.info(f"Copied mono file '{input_file}' to '{mono_output}'.")
            return mono_output, None

        elif channels == 2:
            # Split stereo into left and right channels
            left_channel = audio.split_to_mono()[0]
            right_channel = audio.split_to_mono()[1]

            left_channel.export(left_output, format="wav")
            right_channel.export(right_output, format="wav")

            # Clean up memory
            del audio, left_channel, right_channel
            gc.collect()

            logging.info(f"Split stereo file '{input_file}' into:")
            logging.info(f" - Left channel: '{left_output}'")
            logging.info(f" - Right channel: '{right_output}'")
            return left_output, right_output

    except Exception as e:
        logging.error(f"Splitting error: {e}")
        return None, None

def align_channels(ref_path, input_left, input_right, dest_dir, channel_mode, temp_dir, algorithm, accuracy=3):
    """Align channels with reference using specified mode and algorithm"""
    try:
        # Get reference length first
        ref_audio = AudioSegment.from_file(ref_path)
        ref_length = len(ref_audio.get_array_of_samples())
        if ref_audio.channels == 2:
            ref_length = ref_length // 2
        frame_rate = ref_audio.frame_rate
        
        # Pre-pad input files if needed
        if input_left:
            ensure_matching_length(input_left, ref_length, frame_rate)
                
        if input_right:
            ensure_matching_length(input_right, ref_length, frame_rate)

        recognizer = get_recognizer(algorithm, accuracy)

        # Handle reference channels
        ref_base = os.path.splitext(os.path.basename(ref_path))[0]
        ref_left = os.path.join(temp_dir, f"{ref_base}_L.wav")
        ref_right = os.path.join(temp_dir, f"{ref_base}_R.wav")

        if ref_audio.channels == 1:
            ref_left = ref_path
            ref_right = ref_path
            logging.info("Using mono reference for both channels")
        else:
            if channel_mode == 'L':
                ref_audio.split_to_mono()[0].export(ref_left, format="wav")
                ref_right = ref_left
                logging.info("Using left reference channel for all alignments")
            elif channel_mode == 'R':
                ref_audio.split_to_mono()[1].export(ref_right, format="wav")
                ref_left = ref_right
                logging.info("Using right reference channel for all alignments")
            else:
                ref_audio.split_to_mono()[0].export(ref_left, format="wav")
                ref_audio.split_to_mono()[1].export(ref_right, format="wav")
                logging.info("Using stereo reference channels independently")

        # Clean up memory
        del ref_audio
        gc.collect()

        # Perform alignments
        if input_left:
            align_files(
                filename_a=str(ref_left),
                filename_b=str(input_left),
                destination_path=dest_dir,
                write_extension="_L_aligned.wav",
                write_multi_channel=False,
                recognizer=recognizer
            )

        if input_right:
            align_files(
                filename_a=str(ref_right),
                filename_b=str(input_right),
                destination_path=dest_dir,
                write_extension="_R_aligned.wav",
                write_multi_channel=False,
                recognizer=recognizer
            )

    except Exception as e:
        logging.error(f"Alignment failed: {e}")
        raise

def process_workflow(input_dir, reference_basename, temp_dir, destination_dir, channel_mode='auto', algorithm=DEFAULT_ALGORITHM, accuracy=3):
    """Full workflow: Split -> Align -> Rename -> Merge"""
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(destination_dir, exist_ok=True)

    ref_path = os.path.join(input_dir, reference_basename)
    wav_files = list_root_wav_files(input_dir)
    had_errors = False

    try:
        for wav_file in wav_files:
            if os.path.basename(wav_file) == reference_basename:
                continue

            try:
                input_left, input_right = split_stereo_to_mono(wav_file, temp_dir)
                if input_left is None and input_right is None:
                    had_errors = True
                    continue

                align_channels(ref_path, input_left, input_right, destination_dir, channel_mode, temp_dir, algorithm)
            except Exception as e:
                had_errors = True
                logging.error(f"Failed to process file {wav_file}: {e}")
                continue

        try:
            rename_aligned_files(destination_dir)
        except Exception as e:
            had_errors = True
            logging.error(f"Failed during renaming: {e}")

        try:
            merge_aligned_channels(destination_dir)
        except Exception as e:
            had_errors = True
            logging.error(f"Failed during merging: {e}")

        if had_errors:
            logging.warning("Processing completed with errors")
        else:
            logging.info("Processing completed successfully")

    except Exception as e:
        logging.critical(f"Workflow failed: {e}")
        raise

def ensure_matching_length(audio_file, reference_length, frame_rate):
    """Pre-pad audio file to match reference length if needed"""
    try:
        audio = AudioSegment.from_file(audio_file)
        current_samples = len(audio.get_array_of_samples())
        
        if current_samples < reference_length:
            silence_duration = int((reference_length - current_samples) * 1000 / frame_rate)
            silence = AudioSegment.silent(duration=silence_duration, frame_rate=frame_rate)
            padded_audio = audio + silence
            padded_audio.export(audio_file, format="wav")
            logging.info(f"Pre-padded {os.path.basename(audio_file)} from {current_samples} to {reference_length} samples")
        return True
    except Exception as e:
        logging.error(f"Failed to pre-pad {audio_file}: {e}")
        return False

def rename_aligned_files(destination_dir):
    """Renames aligned mono files to follow the desired naming convention."""
    try:
        for filename in os.listdir(destination_dir):
            if "_L._L_aligned.wav" in filename:
                new_name = filename.replace("_L._L_aligned", "_L_aligned")
                new_path = os.path.join(destination_dir, new_name)
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(
                    os.path.join(destination_dir, filename),
                    new_path
                )
                logging.info(f"Renamed '{filename}' to '{new_name}'.")
            elif "_R._R_aligned.wav" in filename:
                new_name = filename.replace("_R._R_aligned", "_R_aligned")
                new_path = os.path.join(destination_dir, new_name)
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(
                    os.path.join(destination_dir, filename),
                    new_path
                )
                logging.info(f"Renamed '{filename}' to '{new_name}'.")
    except Exception as e:
        logging.error(f"An error occurred during renaming: {e}")
        raise

def merge_aligned_channels(destination_dir):
    """Merges aligned left and right mono channels into stereo files."""
    try:
        aligned_files = [f for f in os.listdir(destination_dir) if f.endswith("_aligned.wav")]
        grouped_files = {}
        
        # Group files by base name
        for f in aligned_files:
            base_name = f.split("_")[0]
            if base_name not in grouped_files:
                grouped_files[base_name] = {}
            if "_L_aligned" in f:
                grouped_files[base_name]["left"] = os.path.join(destination_dir, f)
            if "_R_aligned" in f:
                grouped_files[base_name]["right"] = os.path.join(destination_dir, f)

        for base_name, channels in grouped_files.items():
            if "left" in channels and "right" in channels:
                output_stereo = os.path.join(destination_dir, f"{base_name}_aligned_stereo.wav")
                
                # Load both channels
                left_audio = AudioSegment.from_file(channels["left"])
                right_audio = AudioSegment.from_file(channels["right"])
                
                # Get exact sample counts
                left_samples = len(left_audio.get_array_of_samples())
                right_samples = len(right_audio.get_array_of_samples())
                
                logging.info(f"Initial sample counts - Left: {left_samples}, Right: {right_samples}")
                
                # Use the shorter length to truncate both channels
                target_samples = min(left_samples, right_samples)
                
                # Convert duration to milliseconds for exact truncation
                target_ms = int(target_samples * 1000 / left_audio.frame_rate)
                
                # Truncate both channels to exactly the same length
                left_audio = left_audio[:target_ms]
                right_audio = right_audio[:target_ms]
                
                # Verify final lengths
                final_left = len(left_audio.get_array_of_samples())
                final_right = len(right_audio.get_array_of_samples())
                
                logging.info(f"Final sample counts - Left: {final_left}, Right: {final_right}")
                
                if final_left != final_right:
                    raise ValueError(f"Sample count mismatch after truncation: L={final_left}, R={final_right}")
                
                # Create stereo file
                stereo_audio = AudioSegment.from_mono_audiosegments(left_audio, right_audio)
                stereo_audio.export(output_stereo, format="wav")
                logging.info(f"Merged '{channels['left']}' and '{channels['right']}' into stereo file '{output_stereo}'.")
                
                # Clean up
                os.remove(channels["left"])
                os.remove(channels["right"])
                del left_audio, right_audio, stereo_audio
                gc.collect()
                
    except Exception as e:
        logging.error(f"An error occurred during merging: {e}")
        raise




def main():
    parser = argparse.ArgumentParser(description="Audio alignment workflow")
    parser.add_argument("-i", "--input", required=True, help="Input directory with WAV files")
    parser.add_argument("-r", "--reference", required=True, help="Reference filename")
    parser.add_argument("-t", "--temp", required=True, help="Temporary directory path")
    parser.add_argument("-o", "--destination", required=True, help="Output directory")
    parser.add_argument("-c", "--channel", choices=['L','R','auto'], default='auto',
                        help="Reference channel selection")
    parser.add_argument("-a", "--algorithm", 
                       choices=list(ALGORITHMS.keys()), 
                       default=DEFAULT_ALGORITHM,
                       help=f"Alignment algorithm (default: {DEFAULT_ALGORITHM})")
    parser.add_argument("-acc", "--accuracy", type=int, default=3,
                    help="Accuracy setting for fingerprint algorithm (default: 3)")
    args = parser.parse_args()

    os.makedirs(args.destination, exist_ok=True)
    configure_logging(args.destination)

    try:
        process_workflow(args.input, args.reference, args.temp, args.destination,
                args.channel, args.algorithm, args.accuracy)
    except Exception as e:
        logging.critical(f"Fatal error in main workflow: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()