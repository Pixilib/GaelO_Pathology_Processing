#upload fichier
#conversion du fichier en DICOM
#zippage du fichier

from rest_framework.views import APIView

import subprocess

class ConvertToDicom(APIView):
    def convert_to_dicom(image_path, output_dir):
        """
        Convertit une image en fichier DICOM à l'aide de OrthancWSIDicomizer.
        """
        
        # Commande OrthancWSIDicomizer
        command = [
            "./OrthancWSIDicomizer-2.1.exe", 
            "--input", image_path,
            "--dataset=dataset.json",
            "--folder", output_dir,
        ]

        try:
            subprocess.run(command, check=True ) # Si check = True et que le processus se termine avec un code de sortie non nul, une exception CalledProcessError sera levée.
            return output_dir
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erreur lors de la conversion en DICOM : {e}")


