import os
import shutil
import sys

class PathHandler:
    ASSETS_DIR = "assets"
    STUDENT_IMAGES_DIR = "student_images"
    
    @classmethod
    def get_project_root(cls):
        """Returns the project root directory."""
        # Assuming this file is in logic/ which is one level deep
        # tailored for the specific structure: /media/.../FaceDetentionAttendance/logic/path_handler.py
        # root is /media/.../FaceDetentionAttendance
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def get_images_dir(cls):
        """Returns the absolute path to the student images directory, creating it if needed."""
        root = cls.get_project_root()
        path = os.path.join(root, cls.ASSETS_DIR, cls.STUDENT_IMAGES_DIR)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @classmethod
    def save_student_image(cls, source_path, student_id):
        """
        Copies the source image to the assets folder using a standardized name.
        Returns the relative path to be stored in the DB (e.g., assets/student_images/student_123.jpg).
        """
        if not source_path or not os.path.exists(source_path):
            return None
            
        try:
            images_dir = cls.get_images_dir()
            ext = os.path.splitext(source_path)[1].lower()
            if not ext in ['.jpg', '.jpeg', '.png']:
                ext = '.jpg' # Default fallback
                
            filename = f"student_{student_id}{ext}"
            dest_path = os.path.join(images_dir, filename)
            
            shutil.copy2(source_path, dest_path)
            
            # Return relative path for DB
            # Use forward slashes for cross-platform compatibility
            relative_path = f"{cls.ASSETS_DIR}/{cls.STUDENT_IMAGES_DIR}/{filename}"
            return relative_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None

    @classmethod
    def resolve_path(cls, db_path):
        """
        Resolves a path from the DB to an absolute system path.
        Handles:
        1. Relative paths (assets/...) -> joins with project root
        2. Absolute paths (legacy data) -> returns as is (if exists)
        """
        if not db_path:
            return None
            
        root = cls.get_project_root()
        
        # 1. Try as relative path joined with root
        full_path_relative = os.path.join(root, db_path)
        if os.path.exists(full_path_relative):
            return full_path_relative
            
        # 2. Try as absolute path (Legacy support)
        if os.path.exists(db_path):
            return db_path
            
        # 3. Path invalid/files missing
        return None
