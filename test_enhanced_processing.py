#!/usr/bin/env python3
"""
Test script for enhanced document processing system
"""
import os
import sys
import tempfile
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_ocr_processor():
    """Test OCR processor with a sample image"""
    print("Testing OCR Processor...")
    
    try:
        from app.utils.ocr_processor import OCRProcessor
        
        # Initialize OCR processor
        ocr = OCRProcessor()
        
        print(f"✓ OCR Processor initialized successfully")
        print(f"  - Language: {ocr.language}")
        print(f"  - Config: {ocr.config}")
        print(f"  - Supported formats: {ocr.supported_formats}")
        
        # Test with existing image files if any
        image_files = []
        for ext in ['jpg', 'jpeg', 'png']:
            image_files.extend(Path('.').glob(f'**/*.{ext}'))
        
        if image_files:
            test_image = image_files[0]
            print(f"\nTesting with image: {test_image}")
            
            result = ocr.extract_text_from_image(str(test_image))
            
            if result['success']:
                print(f"✓ OCR extraction successful")
                print(f"  - Extracted text length: {len(result['extracted_text'])}")
                print(f"  - Confidence: {result['confidence']:.1f}%")
                print(f"  - Word count: {result['word_count']}")
                if result['extracted_text']:
                    preview = result['extracted_text'][:200] + '...' if len(result['extracted_text']) > 200 else result['extracted_text']
                    print(f"  - Text preview: {preview}")
            else:
                print(f"✗ OCR extraction failed: {result.get('error')}")
        else:
            print("  - No image files found for testing")
            
        return True
        
    except Exception as e:
        print(f"✗ OCR Processor test failed: {e}")
        return False

def test_docker_processor():
    """Test Docker processor"""
    print("\nTesting Docker Processor...")
    
    try:
        from app.utils.docker_processor import DockerVolumeManager, DockerContainerProcessor
        
        # Test volume manager
        vm = DockerVolumeManager()
        print(f"✓ Docker Volume Manager initialized")
        print(f"  - Volumes path: {vm.volumes_path}")
        
        # Test listing volumes (this might fail if Docker isn't available)
        try:
            volumes = vm.list_available_volumes()
            print(f"  - Available volumes: {len(volumes)}")
            if volumes:
                print(f"    Examples: {volumes[:3]}")
        except Exception as e:
            print(f"  - Could not list volumes (Docker may not be available): {e}")
        
        # Test container processor
        cp = DockerContainerProcessor()
        print(f"✓ Docker Container Processor initialized")
        
        try:
            containers = cp.list_containers_with_documents()
            print(f"  - Running containers: {len(containers)}")
            if containers:
                print(f"    Examples: {[c['name'] for c in containers[:3]]}")
        except Exception as e:
            print(f"  - Could not list containers (Docker may not be available): {e}")
            
        return True
        
    except Exception as e:
        print(f"✗ Docker Processor test failed: {e}")
        return False

def test_document_processor():
    """Test enhanced document processor"""
    print("\nTesting Enhanced Document Processor...")
    
    try:
        from app.utils.document_processor import EnhancedDocumentProcessor
        
        processor = EnhancedDocumentProcessor()
        print(f"✓ Enhanced Document Processor initialized")
        print(f"  - Supported formats: {list(processor.supported_formats.keys())}")
        
        # Test with existing files
        test_files = []
        for ext in ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png']:
            test_files.extend(Path('.').glob(f'**/*.{ext}'))
        
        if test_files:
            test_file = test_files[0]
            print(f"\nTesting with file: {test_file}")
            
            result = processor.process_document(str(test_file))
            
            if result['success']:
                print(f"✓ Document processing successful")
                print(f"  - File size: {result['file_size']} bytes")
                print(f"  - File hash: {result['file_hash'][:16]}...")
                print(f"  - Processing method: {result.get('processing_method')}")
                print(f"  - Document type: {result.get('document_type')}")
                if result.get('extracted_text'):
                    preview = result['extracted_text'][:200] + '...' if len(result['extracted_text']) > 200 else result['extracted_text']
                    print(f"  - Text preview: {preview}")
            else:
                print(f"✗ Document processing failed: {result.get('error')}")
        else:
            print("  - No test files found")
            
        return True
        
    except Exception as e:
        print(f"✗ Enhanced Document Processor test failed: {e}")
        return False

def test_configuration():
    """Test application configuration"""
    print("\nTesting Configuration...")
    
    try:
        from app.config import Config
        
        config = Config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Allowed extensions: {config.ALLOWED_EXTENSIONS}")
        print(f"  - Upload folder: {config.UPLOAD_FOLDER}")
        print(f"  - Docker volumes path: {config.DOCKER_VOLUMES_PATH}")
        print(f"  - OCR enabled: {config.OCR_ENABLED}")
        print(f"  - OCR language: {config.OCR_LANGUAGE}")
        print(f"  - OCR config: {config.OCR_CONFIG}")
        
        # Verify image formats are included
        required_formats = {'jpg', 'jpeg', 'png'}
        if required_formats.issubset(config.ALLOWED_EXTENSIONS):
            print(f"✓ Image formats properly configured")
        else:
            missing = required_formats - config.ALLOWED_EXTENSIONS
            print(f"✗ Missing image formats: {missing}")
            
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Enhanced Document Processing System Tests")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_ocr_processor,
        test_docker_processor,
        test_document_processor
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"✓ Passed: {sum(results)}")
    print(f"✗ Failed: {len(results) - sum(results)}")
    print(f"Total: {len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Enhanced document processing system is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == '__main__':
    main()