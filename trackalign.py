import os
import sys
import argparse
import logging
from pydub import AudioSegment
from audalign import FingerprintRecognizer, align_files

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
            logging.info(f"  - Left channel: '{left_output}'")
            logging.info(f"  - Right channel: '{right_output}'")
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

            logging.info(f"Split stereo file '{input_file}' into:")
            logging.info(f"  - Left channel: '{left_output}'")
            logging.info(f"  - Right channel: '{right_output}'")

            return left_output, right_output

    except Exception as e:
        logging.error(f"Splitting error: {e}")
        return None, None

def align_channels(ref_path, input_left, input_right, dest_dir, channel_mode, temp_dir):
    """Align channels with reference using specified mode"""
    try:
        recognizer = FingerprintRecognizer()
        ref_audio = AudioSegment.from_file(ref_path)
        
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

def rename_aligned_files(destination_dir):
    """Renames aligned mono files to follow the desired naming convention."""
    try:
        for filename in os.listdir(destination_dir):
            if "_L._L_aligned.wav" in filename:
                new_name = filename.replace("_L._L_aligned", "_L_aligned")
                os.rename(
                    os.path.join(destination_dir, filename),
                    os.path.join(destination_dir, new_name),
                )
                logging.info(f"Renamed '{filename}' to '{new_name}'.")
            elif "_R._R_aligned.wav" in filename:
                new_name = filename.replace("_R._R_aligned", "_R_aligned")
                os.rename(
                    os.path.join(destination_dir, filename),
                    os.path.join(destination_dir, new_name),
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
                
                left_audio = AudioSegment.from_file(channels["left"])
                right_audio = AudioSegment.from_file(channels["right"])
                stereo_audio = AudioSegment.from_mono_audiosegments(left_audio, right_audio)
                stereo_audio.export(output_stereo, format="wav")
                
                logging.info(f"Merged '{channels['left']}' and '{channels['right']}' into stereo file '{output_stereo}'.")
                
                os.remove(channels["left"])
                os.remove(channels["right"])
                logging.info(f"Deleted intermediate mono files")

    except Exception as e:
        logging.error(f"An error occurred during merging: {e}")
        raise

def process_workflow(input_dir, reference_basename, temp_dir, destination_dir, channel_mode='auto'):
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
                    
                align_channels(ref_path, input_left, input_right, destination_dir, channel_mode, temp_dir)
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

def main():
    parser = argparse.ArgumentParser(description="Audio alignment workflow")
    parser.add_argument("-i", "--input", required=True, help="Input directory with WAV files")
    parser.add_argument("-r", "--reference", required=True, help="Reference filename")
    parser.add_argument("-t", "--temp", required=True, help="Temporary directory path")
    parser.add_argument("-o", "--destination", required=True, help="Output directory")
    parser.add_argument("-c", "--channel", choices=['L','R','auto'], default='auto',
                      help="Reference channel selection")

    args = parser.parse_args()
    
    # Create directories and configure logging
    os.makedirs(args.destination, exist_ok=True)
    configure_logging(args.destination)

    try:
        process_workflow(args.input, args.reference, args.temp, args.destination, args.channel)
    except Exception as e:
        logging.critical(f"Fatal error in main workflow: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
