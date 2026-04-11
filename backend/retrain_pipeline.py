"""
Continual learning pipeline with Experience Replay and periodic dataset merging.
"""

import os
import shutil
import json
import subprocess
import signal
import time
from pathlib import Path
from datetime import datetime
import random


class RetrainingPipeline:
    """
    Manages automated continual learning with experience replay.
    """
    
    def __init__(self):
        self.storage_dir = Path('storage/training_data')
        self.original_dataset = Path('dataset_orig')  
        self.validation_set = Path('dataset_val')  
        self.model_path = Path('detector_model.pth')
        self.model_backup = Path('detector_model_backup.pth')
        self.log_file = Path('retraining_log.json')
        self.temp_dir = Path('temp_training_data')
        self.archive_dir = Path('storage/archived_rounds')
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Merge old rounds every 5 rounds
        self.MERGE_INTERVAL = 5
    
    def is_ready(self):
        """Check if 100 files collected"""
        from services.data_collector import DataCollector
        collector = DataCollector()
        return collector.is_ready_for_retraining()
    
    def load_samples(self, dataset_path):
        """
        Load image samples from dataset.
        
        Returns:
            list: [(path, label), ...]
        """
        IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
        samples = []
        
        for folder in dataset_path.iterdir():
            if not folder.is_dir():
                continue
            
            label = 0 if folder.name == 'real' else 1
            files = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTS]
            samples.extend((f, label) for f in files)
        
        return samples
    
    def merge_old_rounds_to_dataset(self):
        """
        Every 5 rounds, merge completed rounds into dataset_orig.
        
        This grows the original dataset with high-quality user data.
        """
        from services.data_collector import DataCollector
        collector = DataCollector()
        
        current_round = collector.metadata['current_round']
        
        # Check if it's merge time
        if current_round % self.MERGE_INTERVAL != 0:
            return False
        
        # Calculate which rounds to merge
        # E.g., Round 5 → merge rounds 1-4
        # Round 10 → merge rounds 6-9
        start_round = current_round - self.MERGE_INTERVAL + 1
        end_round = current_round - 1
        
        if start_round < 1:
            return False
        
        print("\n" + "="*70)
        print(f"  MERGING ROUNDS {start_round}-{end_round} INTO ORIGINAL DATASET")
        print("="*70)
        
        merged_count = {'real': 0, 'fake': 0}
        
        for round_num in range(start_round, end_round + 1):
            round_path = self.storage_dir / f'round_{round_num}'
            
            if not round_path.exists():
                print(f"⚠ Round {round_num} not found, skipping")
                continue
            
            print(f"\nMerging round_{round_num}...")
            
            for label in ['real', 'fake']:
                src_dir = round_path / label
                dst_dir = self.original_dataset / label
                
                if not src_dir.exists():
                    continue
                
                # Copy all files
                files = list(src_dir.glob('*'))
                for file in files:
                    dst_path = dst_dir / file.name
                    
                    # Handle duplicates
                    counter = 1
                    while dst_path.exists():
                        dst_path = dst_dir / f"{file.stem}_r{round_num}_{counter}{file.suffix}"
                        counter += 1
                    
                    shutil.copy(file, dst_path)
                    merged_count[label] += 1
            
            # Archive the round
            archive_path = self.archive_dir / f'round_{round_num}.zip'
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'zip',
                round_path
            )
            
            # Delete original round
            shutil.rmtree(round_path)
            print(f"  ✓ Archived to {archive_path.name}")
        
        print(f"\n{'='*70}")
        print(f"  MERGE COMPLETE")
        print(f"  Added to dataset_orig:")
        print(f"    Real: {merged_count['real']} files")
        print(f"    Fake: {merged_count['fake']} files")
        
        # Update dataset stats
        real_count = len(list((self.original_dataset / 'real').glob('*')))
        fake_count = len(list((self.original_dataset / 'fake').glob('*')))
        
        print(f"\n  dataset_orig now contains:")
        print(f"    Real: {real_count} files")
        print(f"    Fake: {fake_count} files")
        print(f"    Total: {real_count + fake_count} files")
        print(f"{'='*70}\n")
        
        return True
    
    def prepare_training_data(self):
        """
        Experience Replay: Mix 80% original + 20% new user data.
        
        Returns:
            Path: Temporary training directory
        """
        from services.data_collector import DataCollector
        collector = DataCollector()
        
        current_round = collector.metadata['current_round']
        new_data_path = self.storage_dir / f'round_{current_round}'
        
        print("\n" + "="*70)
        print("  PREPARING TRAINING DATA (Experience Replay)")
        print("="*70)
        
        # 1. Load original dataset
        print("\n1. Loading original dataset...")
        if not self.original_dataset.exists():
            raise FileNotFoundError(f"Original dataset not found: {self.original_dataset}")
        
        original_samples = self.load_samples(self.original_dataset)
        original_real = [s for s in original_samples if s[1] == 0]
        original_fake = [s for s in original_samples if s[1] == 1]
        
        print(f"   Original: {len(original_real)} real + {len(original_fake)} fake = {len(original_samples)} total")
        
        # 2. Load new user data
        print("\n2. Loading new user data...")
        if not new_data_path.exists():
            raise FileNotFoundError(f"New data not found: {new_data_path}")
        
        new_samples = self.load_samples(new_data_path)
        new_real = [s for s in new_samples if s[1] == 0]
        new_fake = [s for s in new_samples if s[1] == 1]
        
        print(f"   New: {len(new_real)} real + {len(new_fake)} fake = {len(new_samples)} total")
        
        # 3. Experience Replay: Sample 80% from original
        print("\n3. Applying Experience Replay (80% original + 100% new)...")
        
        ORIGINAL_FRACTION = 0.8
        
        sampled_original_real = random.sample(
            original_real, 
            int(len(original_real) * ORIGINAL_FRACTION)
        )
        sampled_original_fake = random.sample(
            original_fake,
            int(len(original_fake) * ORIGINAL_FRACTION)
        )
        
        # 4. Combine
        combined_samples = (
            sampled_original_real + 
            sampled_original_fake + 
            new_real + 
            new_fake
        )
        
        random.shuffle(combined_samples)
        
        print(f"   Sampled original: {len(sampled_original_real)} real + {len(sampled_original_fake)} fake")
        print(f"   Added new: {len(new_real)} real + {len(new_fake)} fake")
        print(f"   Combined total: {len(combined_samples)} samples")
        
        # 5. Create temp directory and copy files
        print("\n4. Creating temporary training directory...")
        
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir()
        
        for label in ['real', 'fake']:
            (self.temp_dir / label).mkdir()
        
        for src_path, label in combined_samples:
            label_name = 'real' if label == 0 else 'fake'
            dst_path = self.temp_dir / label_name / src_path.name
            
            # Handle duplicate names
            counter = 1
            while dst_path.exists():
                dst_path = self.temp_dir / label_name / f"{src_path.stem}_{counter}{src_path.suffix}"
                counter += 1
            
            shutil.copy(src_path, dst_path)
        
        # Summary
        final_real = len(list((self.temp_dir / 'real').glob('*')))
        final_fake = len(list((self.temp_dir / 'fake').glob('*')))
        
        print(f"\n5. Final dataset composition:")
        print(f"   Real: {final_real}")
        print(f"   Fake: {final_fake}")
        print(f"   Total: {final_real + final_fake}")
        print("="*70 + "\n")
        
        return self.temp_dir
    
    def backup_model(self):
        """Backup current model"""
        if self.model_path.exists():
            shutil.copy(self.model_path, self.model_backup)
            print(f"✓ Model backed up to {self.model_backup}")
    
    def train_new_model(self, training_data_dir):
        """
        Run training with continual learning settings.
        """
        print("\n" + "="*70)
        print("  TRAINING NEW MODEL (Continual Learning)")
        print("="*70 + "\n")
        
        # Update train_detector.py to use custom dataset path
        env = os.environ.copy()
        env['DATASET_DIR'] = str(training_data_dir)
        
        try:
            result = subprocess.run(
                ['python3', 'train_detector.py'],
                env=env,
                capture_output=True,
                text=True,
                timeout=7200
            )
            
            if result.returncode == 0:
                print("✓ Training completed")
                # Print last 20 lines of output
                lines = result.stdout.split('\n')
                for line in lines[-20:]:
                    if line.strip():
                        print(line)
                return True
            else:
                print(f"✗ Training failed")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Training timeout")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def validate_model(self, model_path, dataset_path, dataset_name):
        """
        Validate model on specific dataset.
        
        Returns:
            float: Accuracy percentage
        """
        if not dataset_path.exists():
            print(f"⚠ {dataset_name} validation set not found at {dataset_path}")
            return None
        
        from models.nn_detector import NNDetector
        
        print(f"\nValidating on {dataset_name}...")
        
        try:
            detector = NNDetector(model_path)
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            return None
        
        correct = 0
        total = 0
        real_correct = 0
        real_total = 0
        fake_correct = 0
        fake_total = 0
        
        for label in ['real', 'fake']:
            label_dir = dataset_path / label
            if not label_dir.exists():
                continue
            
            for img_path in label_dir.glob('*'):
                try:
                    result = detector.predict(str(img_path))
                    predicted = result['prediction']
                    
                    is_correct = (label == 'real' and predicted == 'real') or \
                                (label == 'fake' and predicted == 'fake')
                    
                    if is_correct:
                        correct += 1
                        if label == 'real':
                            real_correct += 1
                        else:
                            fake_correct += 1
                    
                    total += 1
                    if label == 'real':
                        real_total += 1
                    else:
                        fake_total += 1
                        
                except Exception as e:
                    print(f"  Error on {img_path.name}: {e}")
                    continue
        
        if total == 0:
            print(f"  No valid files found")
            return None
        
        accuracy = (correct / total * 100)
        real_acc = (real_correct / real_total * 100) if real_total > 0 else 0
        fake_acc = (fake_correct / fake_total * 100) if fake_total > 0 else 0
        
        print(f"  Overall: {correct}/{total} correct ({accuracy:.2f}%)")
        print(f"  Real: {real_correct}/{real_total} correct ({real_acc:.2f}%)")
        print(f"  Fake: {fake_correct}/{fake_total} correct ({fake_acc:.2f}%)")
        
        return accuracy
    
    def should_deploy(self, old_acc, new_acc):
        """
        Deployment criteria: no significant degradation.
        
        Tolerance: 2% drop allowed
        """
        TOLERANCE = 2.0
        
        if new_acc is None:
            return False, "Validation failed"
        
        if old_acc is not None:
            degradation = old_acc - new_acc
            if degradation > TOLERANCE:
                return False, f"Performance degraded by {degradation:.2f}% (tolerance: {TOLERANCE}%)"
        
        return True, "Performance acceptable"
    
    def reload_backend(self):
        """
        Reload Gunicorn backend to load new model.
        Sends SIGHUP signal for graceful reload.
        
        Returns:
            bool: Success status
        """
        pidfile = Path('/tmp/gunicorn_deepfake.pid')
        
        if not pidfile.exists():
            print("  ⚠ PID file not found - backend may not be running")
            return False
        
        try:
            pid = int(pidfile.read_text().strip())
            
            # Send SIGHUP for graceful reload
            os.kill(pid, signal.SIGHUP)
            
            # Wait a moment for reload
            time.sleep(2)
            
            # Verify process still exists
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except OSError:
                print("  ⚠ Backend process not found after reload")
                return False
                
        except ValueError:
            print("  ⚠ Invalid PID in file")
            return False
        except ProcessLookupError:
            print("  ⚠ Backend process not found")
            return False
        except PermissionError:
            print("  ⚠ Permission denied to reload backend")
            return False
        except Exception as e:
            print(f"  ⚠ Error reloading backend: {e}")
            return False
    
    def log_retraining(self, event, details):
        """Log event to file"""
        if self.log_file.exists():
            logs = json.loads(self.log_file.read_text())
        else:
            logs = []
        
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'details': details
        })
        
        self.log_file.write_text(json.dumps(logs, indent=2))
    
    def run_retraining(self):
        """
        Main continual learning pipeline.
        """
        print("\n" + "="*70)
        print("  🔄 CONTINUAL LEARNING RETRAINING PIPELINE")
        print("="*70 + "\n")
        
        try:
            # Step 1: Check readiness
            print("Step 1/9: Checking readiness...")
            if not self.is_ready():
                print("❌ Not ready (need 100 files)")
                return False
            print("✓ Ready\n")
            
            # Step 2: Check for round merge
            print("Step 2/9: Checking for round merge...")
            merged = self.merge_old_rounds_to_dataset()
            if merged:
                print("✓ Old rounds merged into dataset_orig")
            else:
                print("✓ No merge needed (not at 5-round interval)")
            print()
            
            self.log_retraining('START', {'status': 'initiated'})
            
            # Step 3: Prepare data
            print("Step 3/9: Preparing training data...")
            train_dir = self.prepare_training_data()
            
            # Step 4: Backup model
            print("Step 4/9: Backing up current model...")
            self.backup_model()
            print()
            
            # Step 5: Validate old model
            print("Step 5/9: Validating current model...")
            old_acc = self.validate_model(
                self.model_path,
                self.validation_set,
                "dataset_val"
            )
            print()
            
            # Step 6: Train
            print("Step 6/9: Training new model...")
            success = self.train_new_model(train_dir)
            
            if not success:
                self.log_retraining('FAILED', {'reason': 'training_error'})
                shutil.rmtree(train_dir)
                return False
            print()
            
            # Step 7: Validate new model
            print("Step 7/9: Validating new model...")
            new_acc = self.validate_model(
                self.model_path,
                self.validation_set,
                "dataset_val"
            )
            print()
            
            # Step 8: Deployment decision
            print("Step 8/9: Deployment decision...")
            print(f"\n  Validation Results:")
            print(f"    Old model: {old_acc:.2f}%" if old_acc else "    Old model: N/A")
            print(f"    New model: {new_acc:.2f}%" if new_acc else "    New model: N/A")
            
            if old_acc and new_acc:
                change = new_acc - old_acc
                print(f"    Change: {change:+.2f}%")
            
            should_deploy, reason = self.should_deploy(old_acc, new_acc)
            
            print(f"\n  Decision: {reason}")
            
            if should_deploy:
                print("\n✓ Deploying new model")
                
                self.log_retraining('SUCCESS', {
                    'old_accuracy': round(old_acc, 2) if old_acc else None,
                    'new_accuracy': round(new_acc, 2) if new_acc else None,
                    'deployed': True,
                    'reason': reason
                })
                
                # Reload backend to load new model
                print("\nReloading backend...")
                reload_success = self.reload_backend()
                if reload_success:
                    print("✓ Backend reloaded with new model")
                else:
                    print("⚠ Backend reload failed - manual restart required")
                
                # Start new round
                from services.data_collector import DataCollector
                collector = DataCollector()
                collector.start_new_round()
                print("✓ Started new collection round")
                
                result = True
            else:
                print(f"\n❌ Rejecting new model: {reason}")
                
                # Rollback
                if self.model_backup.exists():
                    shutil.copy(self.model_backup, self.model_path)
                    print("✓ Rolled back to previous model")
                
                self.log_retraining('REJECTED', {
                    'old_accuracy': round(old_acc, 2) if old_acc else None,
                    'new_accuracy': round(new_acc, 2) if new_acc else None,
                    'deployed': False,
                    'reason': reason
                })
                
                result = False
            
            # Step 9: Cleanup
            print("\nStep 9/9: Cleanup...")
            shutil.rmtree(train_dir)
            print("✓ Cleaned up temporary files")
            
            print("\n" + "="*70)
            print(f"  {'✓ RETRAINING COMPLETED' if result else '✗ RETRAINING REJECTED'}")
            print("="*70 + "\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            
            self.log_retraining('ERROR', {'error': str(e)})
            
            if 'train_dir' in locals() and train_dir.exists():
                shutil.rmtree(train_dir)
            
            return False


if __name__ == "__main__":
    pipeline = RetrainingPipeline()
    success = pipeline.run_retraining()
    exit(0 if success else 1)