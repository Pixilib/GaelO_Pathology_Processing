from pathlib import Path
from rest_framework.request import Request
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
import subprocess
import os
import zipfile
import uuid
import tempfile
from gaelo_pathology_processing.services.file_helper import get_file, move_to_storage

class DicomView(APIView):
    """
    Gestion des téléchargements d'images et des métadonnées associées.
    """

    def post(self, request : Request) -> HttpResponse:
        """Télécharge une image, génère un fichier DICOM"""
        try:
            # Validation de l'image
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({"error": "Aucune image n'a été envoyée."}, status=400)

            with tempfile.TemporaryDirectory() as temp_dir:
                base_output_dir = Path(temp_dir) / 'dicoms'
                base_output_dir.mkdir(parents=True, exist_ok=True)

                # Chemin pour l'image temporaire
                temp_image_path = Path(temp_dir) / image_file.name
                with open(temp_image_path, 'wb') as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)

                # Conversion en DICOM
                unique_id, result = self.convert_to_dicom(temp_image_path, base_output_dir)

                # ZIP du dossier DICOM
                zip_file_name = f"{unique_id}.zip"
                zip_temp_path = Path(temp_dir) / zip_file_name
                self.zip_dicom(result, zip_temp_path)

                # Déplacer le ZIP dans le stockage
                move_to_storage('dicoms', zip_temp_path, zip_file_name)

                return Response({"message": "Conversion réussie", "id": unique_id, "output_dir": str(result)}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)    
    
    
    def convert_to_dicom(self, image_path : str, base_output_dir : str) -> str:
        """
        Convertit une image en fichier DICOM à l'aide de OrthancWSIDicomizer.
        """
        unique_id = str(uuid.uuid4())
        output_dir = Path(base_output_dir) / unique_id
        os.makedirs(output_dir, exist_ok=True)
        executable_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'OrthancWSIDicomizer-2.1.exe' )
        
        # Commande pour générer le dataset JSON
        # dataset_file = "dataset.json"
        # dataset_command = [
        #     executable_path,
        #     "--sample-dataset",
            
        # ]

        # Commande OrthancWSIDicomizer
        command = [
            executable_path,
            "--openslide=libopenslide-1.dll", 
            image_path,
            "--dataset=dataset.json",
            "--folder", 
            output_dir
        ]

        try:
            # Générer dataset.json
            # with open(dataset_file, "w") as f:
            #     subprocess.run(dataset_command, stdout=f, check=True)

            #Lancer la conversion
            subprocess.run(command, check=True ) # Si check = True et que le processus se termine avec un code de sortie non nul, une exception CalledProcessError sera levée.
            return unique_id, output_dir
        except subprocess.CalledProcessError as e:
            raise APIException(f"Erreur lors de la conversion en DICOM : {e}")
    
    
    def get(self, request: Request, id: str) -> HttpResponse:
        """Récupère un ZIP contenant le dossier DICOM associé à l'ID donné et le télécharge depuis le storage."""
        try:
            # Accéder au storage 'dicoms'
            file = get_file('dicoms',id + '.zip' )     

            # Crée la réponse pour le téléchargement
            response = FileResponse(file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{id}.zip"'
            response['Content-Type'] = 'application/zip'

            return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)
            
    def zip_dicom(self, folder_path, zip_path):
        """
        Crée un fichier ZIP contenant tout le contenu du dossier spécifié.
        """
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Parcourir tous les fichiers et dossiers dans le dossier
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = os.path.relpath(file_path, start=folder_path)
                        zipf.write(file_path, arcname=arcname)
            print(f"ZIP créé : {zip_path}")
        except Exception as e:
            print(f"Erreur lors de la création du ZIP : {e}")