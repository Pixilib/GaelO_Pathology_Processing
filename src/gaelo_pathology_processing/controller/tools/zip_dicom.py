import zipfile
import os
from ...models import DicomImage
from django.http import HttpResponse


def zip_dicom(request, unique_id):
    """
    Génère un fichier ZIP contenant le DICOM et le renvoie en réponse.
    """

    try:
        image = DicomImage.object.get(unique_id= unique_id)
        zip_path = os.path.join('', f'{unique_id}.zip')

    #creation du fichier zip
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(image.dicom_file.path, arcname=f'{unique_id}.dcm')

        #envoi du fichier zip en reponse
        with open(zip_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={unique_id}.zip'
            return response
    except DicomImage.DoesNotExist:
        return HttpResponse("Image not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)