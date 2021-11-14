import os
import uuid
import traceback
from Model import db
from flask_restful import Resource
from flask import request, current_app
from flask_jwt_extended import jwt_required
from Model import FileModel, FileModelSchema
from utils.utils import get_extension_from_path, delete_file


class File(Resource):

    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}
    
    def sanitize_filename(self, filename):
        return filename.upper()

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def get_file_size(self, upload_folder, filename):
        file_length = os.stat(f"{upload_folder}/{filename}").st_size
        
        return file_length
    
    def insert_on_database(self, data):
        try:
            model = FileModel(
                file_id=data['id'],
                filename=data['filename'],
                extension=data['extension'],
                size=data['size']
            )

            db.session.add(model)
            db.session.commit()

            schema = FileModelSchema()
            data = schema.dump(model)

            return data
        except:
            traceback.print_exc()
            return None


    @jwt_required
    def post(self):
        try:
            if 'file' not in request.files:
                return {'msg': 'No file part'}, 500
            file = request.files['file']
            typeOfData = request.args.get('typeOfData').upper()
            file.filename = self.sanitize_filename(file.filename)
            print('fluxo' not in file.filename, file.filename, typeOfData)
            if typeOfData == 'WIFI' and 'HOTSPOT' not in file.filename:
                return {'msg': 'not a valid file for wifi'}, 500
            if typeOfData == 'FLOW' and 'FLUXO' not in file.filename:
                return {'msg': 'not a valid file for flow'}, 500
            if typeOfData == 'SALES' and 'TICKET' not in file.filename:
                return {'msg': 'not a valid file for sales'}, 500
            extension = get_extension_from_path(file.filename)
            upload_folder = f"{current_app.config.get('PRE_PROCESSING_RAW')}/{typeOfData}"
            if file and self.allowed_file(file.filename):
                file.save(os.path.join(upload_folder, file.filename))
            else:
                return {'msg': 'Extension file invalid'}, 500
            
            data = {
                'id': file.filename,
                'filename': file.filename,
                'extension': extension.replace('.', ''),
                'size': self.get_file_size(upload_folder, file.filename),
                'url': f"{upload_folder}/{file.filename}"
            }

            model = self.insert_on_database(data)

            return model
        except:
            traceback.print_exc()
            return {'msg': f"Error on save file"}, 500

    @jwt_required
    def delete(self, key):
        try:
            typeOfData = request.args.get('typeOfData')
            print(typeOfData)
            file = FileModel.query.filter_by(id=key).first()
            path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/{typeOfData}/{file.filename}"
            print(path)
            delete_file(path)
            
            db.session.delete(file)
            db.session.commit()

            return True
        except:
            traceback.print_exc()
            return {'msg': f"Error on delete file"}, 500
