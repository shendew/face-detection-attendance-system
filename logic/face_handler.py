
import face_recognition
import numpy as np

class FaceHandler:
    @staticmethod
    def encode_face(image_path):
        """
        Loads an image and returns the face encoding.
        Assumes the image contains exactly one face.
        Returns the encoding as a numpy array, or None if no face found.
        """
        try:
            image = face_recognition.load_image_file(image_path)
            # Get face encodings for the image
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                return encodings[0]
            else:
                return None
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None

    @staticmethod
    def match_face(unknown_encoding, known_encodings_dict, tolerance=0.5):
        """
        Matches an unknown face encoding against a dictionary of known encodings.
        known_encodings_dict: {user_id: encoding_list, ...}
        Returns the user_id of the match if found, else None.
        """
        if unknown_encoding is None or not known_encodings_dict:
            return None

        known_ids = list(known_encodings_dict.keys())
        known_encodings = list(known_encodings_dict.values())

        # compare_faces returns a list of True/False
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=tolerance)
        face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            return known_ids[best_match_index]
            
        return None
        
    @staticmethod
    def convert_encoding_to_list(encoding):
        """Converts numpy array encoding to list for MongoDB storage"""
        if encoding is not None:
            return encoding.tolist()
        return None
         
    @staticmethod
    def convert_list_to_encoding(list_encoding):
        """Converts list from MongoDB back to numpy array"""
        if list_encoding is not None:
            return np.array(list_encoding)
        return None
