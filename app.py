import os
import subprocess
import zipfile
import logging
from flask import Flask, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'zip', 'exe'}

# 設置日誌
logging.basicConfig(level=logging.INFO)

def allowed_file(filename):
    """檢查文件是否允許的類型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_zip(zip_path, extract_to):
    """解壓 ZIP 文件"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        logging.error(f"解壓失敗: {e}")
        return False

def package_to_exe(source_dir, output_dir, exe_name):
    """使用 PyInstaller 將解壓後的文件打包成 EXE，EXE 名字來自 ZIP 檔名"""
    try:
        subprocess.run(
            ['pyinstaller', '--onefile', '--distpath', output_dir, f'{source_dir}/main.py'],
            check=True
        )
        exe_file = os.path.join(output_dir, exe_name)
        os.rename(os.path.join(output_dir, 'main.exe'), exe_file)
        logging.info(f"EXE 文件 {exe_file} 打包成功")
        return True
    except Exception as e:
        logging.error(f"打包錯誤: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('沒有文件被選擇')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('未選擇文件')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 處理 ZIP 文件
        if filename.endswith('.zip'):
            extract_to = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted')
            if extract_zip(file_path, extract_to):
                flash(f"{filename} 解壓成功")

                # 使用 ZIP 文件名來命名 EXE
                exe_name = filename.rsplit('.', 1)[0] + '.exe'
                if package_to_exe(extract_to, app.config['UPLOAD_FOLDER'], exe_name):
                    flash(f"{exe_name} 打包成功")
                else:
                    flash(f"{exe_name} 打包失敗")
            else:
                flash(f"解壓失敗: {filename}")
        elif filename.endswith('.exe'):
            # 執行 EXE 文件
            try:
                subprocess.Popen([file_path], shell=True)
                flash(f"已成功運行 {filename}")
            except Exception as e:
                logging.error(f"運行錯誤: {e}")
                flash(f"運行錯誤: {str(e)}")
        return redirect(url_for('index'))
    else:
        flash('不支持的文件類型，僅支持 .exe 和 .zip 文件')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # 確保上傳文件夾存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True,port=10000, host='0.0.0.0')
