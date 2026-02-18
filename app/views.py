import os
from fastapi import UploadFile, Response, status, HTTPException
from werkzeug.utils import secure_filename  

from app.config import UPLOAD_FOLDER


def upload_files(files: list[UploadFile], response: Response):
    try:
        for file in files:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            if file:
                filename = secure_filename(file.filename)
                if not filename.rsplit('.', 1)[1].lower() in {'pdf'}:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid file type. Please upload pdf's"
                    )

                file_path = os.path.join(UPLOAD_FOLDER, filename)
 
                with open(file_path, "wb") as f:
                    f.write(file.file.read())
        
        response.status_code = status.HTTP_200_OK
        return {"message": "Successfully uploaded file(s)"}

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def files(response: Response):
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            return {"files": []}

        files = [
            f for f in os.listdir(UPLOAD_FOLDER)
            if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
        ]

        response.status_code = status.HTTP_200_OK
        return {
            "files": files
        }
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def delete_file(filename: str, response: Response):
    try:
        if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            os.remove(os.path.join(UPLOAD_FOLDER, filename))

        response.status_code = status.HTTP_200_OK
        return {
            "message": "File has been removed"
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    