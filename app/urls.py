from app import app
from app import views, rag

app.add_api_route("/upload", endpoint=views.upload_files, methods=['POST'])
app.add_api_route("/files", endpoint=views.files, methods=['GET'])
app.add_api_route("/chat", endpoint=rag.chat, methods=['POST'])
app.add_api_route("/delete_file", endpoint=views.delete_file, methods=['DELETE'])
