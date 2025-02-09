#!/usr/bin/env python3
import os
import shutil
import datetime
import zipfile
import yaml
import logging
from typing import Dict, List

class LogManager:
    def __init__(self, logs_dir: str, config_path: str):
        """
        Initialize Log Manager
        
        :param logs_dir: Directory containing log files
        :param config_path: Path to log management configuration
        """
        self.logs_dir = logs_dir
        self.config = self._load_config(config_path)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename=os.path.join(logs_dir, 'log_management.log')
        )
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file
        
        :param config_path: Path to config file
        :return: Configuration dictionary
        """
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)
    
    def _get_log_files(self) -> List[str]:
        """
        Retrieve all log files
        
        :return: List of log file paths
        """
        log_files = []
        for root, _, files in os.walk(self.logs_dir):
            log_files.extend([
                os.path.join(root, f) for f in files 
                if f.endswith('_chat_log.md')
            ])
        return log_files
    
    def anonymize_logs(self, log_files: List[str]):
        """
        Anonymize sensitive information in log files
        
        :param log_files: List of log file paths
        """
        if not self.config.get('anonymization', {}).get('enabled', False):
            return
        
        anonymization_fields = self.config['anonymization'].get('fields_to_anonymize', [])
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Simple anonymization
            for field in anonymization_fields:
                if field == 'personal_identifiers':
                    content = content.replace('Chat ID: ', 'Chat ID: [ANONYMIZED]')
                elif field == 'sensitive_data':
                    # Replace potential sensitive data patterns
                    content = content.replace('path/to/', '[REDACTED]/')
            
            with open(log_file, 'w') as f:
                f.write(content)
            
            logging.info(f"Anonymized log file: {log_file}")
    
    def compress_old_logs(self):
        """
        Compress logs older than the compression threshold
        """
        compression_threshold = self.config['log_management'].get('compression_threshold', 365)
        retention_period = self.config['log_management'].get('retention_period', 2)
        
        current_time = datetime.datetime.now()
        log_files = self._get_log_files()
        
        for log_file in log_files:
            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
            days_since_modification = (current_time - file_mod_time).days
            
            # Determine if log should be compressed or deleted
            if days_since_modification > compression_threshold:
                # Compress logs
                year = file_mod_time.year
                month = file_mod_time.strftime('%B')
                archive_dir = os.path.join(self.logs_dir, str(year), month)
                os.makedirs(archive_dir, exist_ok=True)
                
                archive_path = os.path.join(archive_dir, f"{os.path.basename(log_file)}.zip")
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(log_file, arcname=os.path.basename(log_file))
                
                logging.info(f"Compressed log file: {log_file} to {archive_path}")
                
                # Delete original log file
                os.remove(log_file)
            
            # Delete logs beyond retention period
            if days_since_modification > (retention_period * 365):
                os.remove(log_file)
                logging.info(f"Deleted log file beyond retention period: {log_file}")
    
    def validate_log_size(self):
        """
        Validate and manage log file sizes
        """
        max_log_size = self.config['log_management'].get('max_log_size', 10) * 1024 * 1024  # MB to bytes
        log_files = self._get_log_files()
        
        for log_file in log_files:
            file_size = os.path.getsize(log_file)
            
            if file_size > max_log_size:
                # Split large log files
                with open(log_file, 'r') as f:
                    content = f.readlines()
                
                # Split content into smaller chunks
                chunk_size = len(content) // 2
                first_half = content[:chunk_size]
                second_half = content[chunk_size:]
                
                # Write first half
                with open(f"{log_file}_part1.md", 'w') as f:
                    f.writelines(first_half)
                
                # Write second half
                with open(f"{log_file}_part2.md", 'w') as f:
                    f.writelines(second_half)
                
                # Remove original large file
                os.remove(log_file)
                
                logging.warning(f"Split large log file: {log_file}")
    
    def run_maintenance(self):
        """
        Execute full log management maintenance
        """
        try:
            # Get all log files
            log_files = self._get_log_files()
            
            # Anonymize logs
            self.anonymize_logs(log_files)
            
            # Compress old logs
            self.compress_old_logs()
            
            # Validate log sizes
            self.validate_log_size()
            
            logging.info("Log maintenance completed successfully")
        except Exception as e:
            logging.error(f"Log maintenance failed: {str(e)}")
            raise

# Main execution
if __name__ == '__main__':
    import sys
    
    config_path = '/path/to/aiqleads/config/log_config.yaml'
    logs_dir = '/path/to/aiqleads/logs'
    
    log_manager = LogManager(logs_dir, config_path)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'maintenance':
            log_manager.run_maintenance()
        elif command == 'compress':
            log_manager.compress_old_logs()
        elif command == 'anonymize':
            log_files = log_manager._get_log_files()
            log_manager.anonymize_logs(log_files)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("Usage: log_management.py [maintenance|compress|anonymize]")
        sys.exit(1)