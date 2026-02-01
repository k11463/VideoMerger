import os
import re
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# 嘗試獲取 ffmpeg 路徑
def get_ffmpeg_path():
    # 1. 優先檢查程式碼所在資料夾是否有 ffmpeg.exe (適合隨附檔案)
    local_ffmpeg = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # 2. 其次嘗試檢查 MoviePy 的環境設定
    try:
        from moviepy.config import get_setting
        path = get_setting("FFMPEG_BINARY")
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    # 3. 最後才嘗試系統環境變數
    return "ffmpeg"

class VideoMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("影片自動合併工具 - 終極穩定版")
        self.root.geometry("620x550")
        
        self.input_paths = []
        self.output_dir = ""

        tk.Label(root, text="影片自動合併系統 (FFmpeg 核心)", font=('Arial', 14, 'bold')).pack(pady=10)
        tk.Button(root, text="1. 選取影片檔案", command=self.select_files, height=2, width=30).pack(pady=5)
        self.lbl_count = tk.Label(root, text="尚未選取檔案", fg="blue")
        self.lbl_count.pack()

        tk.Button(root, text="2. 選取儲存資料夾", command=self.select_output, height=2, width=30).pack(pady=5)
        self.lbl_path = tk.Label(root, text="尚未設定路徑", fg="green", wraplength=500)
        self.lbl_path.pack()

        tk.Label(root, text="處理日誌:").pack(anchor="w", padx=50)
        self.log_area = scrolledtext.ScrolledText(root, height=12, width=70)
        self.log_area.pack(padx=20, pady=5)

        self.btn_run = tk.Button(root, text="開始執行合併", command=self.process, bg="#28a745", fg="white", font=('Arial', 12, 'bold'), height=2, width=20)
        self.btn_run.pack(pady=10)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.root.update()

    def select_files(self):
        files = filedialog.askopenfilenames(title="選取影片", filetypes=[("影片格式", "*.mp4 *.mov *.avi *.mkv")])
        if files:
            self.input_paths = list(files)
            self.lbl_count.config(text=f"已選取 {len(self.input_paths)} 個檔案")

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir = path
            self.lbl_path.config(text=f"儲存至: {path}")

    def get_group_id(self, filename):
        name = os.path.splitext(filename)[0]
        while " - 複製" in name:
            name = name.replace(" - 複製", "")
        return name.strip()

    def process(self):
        if not self.input_paths or not self.output_dir:
            messagebox.showerror("錯誤", "請選取檔案與路徑！")
            return

        groups = {}
        for p in self.input_paths:
            gid = self.get_group_id(os.path.basename(p))
            if gid not in groups: groups[gid] = []
            groups[gid].append(p)

        self.log(">>> 開始執行任務 (無損合併模式)...")
        success_count = 0
        ffmpeg_bin = get_ffmpeg_path()

        for gid, paths in groups.items():
            if len(paths) < 2: continue
            
            paths.sort(key=lambda x: (len(os.path.basename(x)), x))
            self.log(f"合併組別 [{gid}]...")
            
            # 建立 FFmpeg 清單
            list_file = os.path.join(self.output_dir, f"list_{success_count}.txt")
            try:
                with open(list_file, "w", encoding="utf-8") as f:
                    for p in paths:
                        # 修正 f-string 語法錯誤：先處理好字串再放入
                        safe_path = p.replace("'", "'\\''")
                        f.write("file '" + safe_path + "'\n")

                clean_gid = re.sub(r'[\\/*?:"<>|]', "", gid).replace(" ", "_")
                output_filename = f"Final_{clean_gid}.mp4"
                save_path = os.path.join(self.output_dir, output_filename)

                cmd = [
                    ffmpeg_bin, "-y", "-f", "concat", "-safe", "0",
                    "-i", list_file, "-c", "copy", save_path
                ]

                # 執行合併，隱藏黑視窗
                si = None
                if os.name == 'nt':
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=si)
                
                if result.returncode == 0:
                    self.log(f"✅ 完成：{output_filename}")
                    success_count += 1
                else:
                    self.log(f"❌ 失敗 [{gid}]: {result.stderr[:100]}")
            
            except Exception as e:
                self.log(f"❌ 錯誤 [{gid}]: {str(e)}")
            finally:
                if os.path.exists(list_file):
                    os.remove(list_file)

        messagebox.showinfo("完成", f"任務結束，共合併 {success_count} 組影片！")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMergerApp(root)
    root.mainloop()