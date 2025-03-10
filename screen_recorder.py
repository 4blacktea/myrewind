import os
import subprocess
import time
from datetime import datetime
import ffmpeg
from PIL import Image
import json
import requests
import signal
import sys
from keyframe_analyzer import KeyframeAnalyzer
from video_player import VideoPlayer

class ScreenRecorder:
    def __init__(self, output_dir="recordings", keyframes_dir="keyframes"):
        self.output_dir = output_dir
        self.keyframes_dir = keyframes_dir
        self.metadata_file = "recording_metadata.json"
        self.ensure_directories()
        self.load_metadata()
        self.recording_process = None
        self.is_recording = False
        self.is_paused = False
        self.current_video_file = None
        self.keyframe_analyzer = KeyframeAnalyzer(keyframes_dir)
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def handle_interrupt(self, signum, frame):
        """处理中断信号"""
        if self.is_recording:
            self.stop_recording()
            if self.current_video_file:
                self.process_recording(self.current_video_file)
        sys.exit(0)

    def ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.keyframes_dir, exist_ok=True)

    def load_metadata(self):
        """加载或创建元数据文件"""
        try:
            if os.path.exists(self.metadata_file):
                # 检查文件大小
                if os.path.getsize(self.metadata_file) == 0:
                    print(f"元数据文件 {self.metadata_file} 为空，创建新的元数据列表")
                    self.metadata = []
                    self.save_metadata()
                    return
                
                # 尝试读取文件内容
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"元数据文件 {self.metadata_file} 为空，创建新的元数据列表")
                        self.metadata = []
                        self.save_metadata()
                        return
                    
                    try:
                        self.metadata = json.loads(content)
                        print(f"成功加载元数据，包含 {len(self.metadata)} 条记录")
                    except json.JSONDecodeError as e:
                        print(f"元数据文件格式错误: {str(e)}")
                        print("创建新的元数据列表")
                        self.metadata = []
                        self.save_metadata()
            else:
                print(f"元数据文件 {self.metadata_file} 不存在，创建新文件")
                self.metadata = []
                self.save_metadata()
        except Exception as e:
            print(f"加载元数据时出错: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            print("创建新的元数据列表")
            self.metadata = []
            self.save_metadata()

    def save_metadata(self):
        """保存元数据到文件"""
        try:
            print(f"正在保存元数据到文件: {self.metadata_file}")
            print(f"元数据内容: {self.metadata}")
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            print("元数据保存成功")
        except Exception as e:
            print(f"保存元数据时出错: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")

    def check_screen_permission(self):
        """检查屏幕录制权限"""
        try:
            # 尝试列出设备，如果成功则说明有权限
            result = subprocess.run(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'],
                                 capture_output=True, text=True)
            return "AVFoundation video devices:" in result.stderr
        except Exception:
            return False

    def request_screen_permission(self):
        """请求屏幕录制权限"""
        print("\n=== 屏幕录制权限设置 ===")
        print("1. 打开系统偏好设置")
        print("2. 点击'安全性与隐私'")
        print("3. 选择'隐私'标签")
        print("4. 在左侧列表中选择'屏幕录制'")
        print("5. 确保'终端'或'Python'已勾选")
        print("6. 如果没有勾选，请勾选并输入管理员密码")
        print("7. 完成后按回车继续")
        input("\n请按照上述步骤设置权限，完成后按回车继续...")

    def start_recording(self, duration=None):
        """开始录屏"""
        # 检查权限
        if not self.check_screen_permission():
            self.request_screen_permission()
            if not self.check_screen_permission():
                print("未获得屏幕录制权限，无法继续")
                return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"recording_{timestamp}.mp4")
        
        # 构建ffmpeg命令
        command = [
            'ffmpeg', '-f', 'avfoundation',
            '-capture_cursor', '1',  # 捕获鼠标光标
            '-capture_mouse_clicks', '1',  # 捕获鼠标点击
            '-i', '0',  # 在macOS上，0代表屏幕捕获
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-y',  # 覆盖已存在的文件
        ]

        if duration:
            command.extend(['-t', str(duration)])
        
        command.append(output_file)
        
        try:
            self.recording_process = subprocess.Popen(command)
            self.is_recording = True
            self.is_paused = False
            self.current_video_file = output_file
            return output_file
        except Exception as e:
            print(f"录制出错: {str(e)}")
            return None

    def pause_recording(self):
        """暂停录制"""
        if self.is_recording and not self.is_paused:
            self.recording_process.send_signal(signal.SIGSTOP)
            self.is_paused = True
            print("录制已暂停")

    def resume_recording(self):
        """继续录制"""
        if self.is_recording and self.is_paused:
            self.recording_process.send_signal(signal.SIGCONT)
            self.is_paused = False
            print("录制已继续")

    def stop_recording(self):
        """停止录制"""
        if self.is_recording:
            self.recording_process.send_signal(signal.SIGINT)
            self.recording_process.wait()
            self.is_recording = False
            self.is_paused = False
            print("录制已停止")

    def process_recording(self, video_file):
        """处理录制的视频"""
        print(f"正在处理视频: {video_file}")
        keyframe_files, analyses = self.keyframe_analyzer.process_video(video_file)
        if not keyframe_files or not analyses:
            print("处理视频失败：无法提取关键帧或分析失败")
            return

        # 保存元数据
        metadata_entry = {
            'timestamp': datetime.now().isoformat(),
            'video_file': video_file,
            'keyframe_files': keyframe_files,
            'analyses': analyses
        }
        print(f"保存元数据: {metadata_entry}")
        self.metadata.append(metadata_entry)
        self.save_metadata()
        print("元数据已保存")

    def record_and_analyze(self, duration=None):
        """录制屏幕并分析关键帧"""
        print("开始录制...")
        
        video_file = self.start_recording(duration)
        if not video_file:
            return

        try:
            while self.is_recording:
                print("\r录制中... 按Ctrl+C停止", end="", flush=True)
                time.sleep(1)
            print("\n录制完成！")
        except KeyboardInterrupt:
            self.stop_recording()
            print("\n录制已停止！")

        self.process_recording(video_file)

    def search_recordings(self, query):
        """搜索录制内容"""
        results = []
        for entry in self.metadata:
            # 检查所有分析结果
            if 'analyses' in entry:
                for analysis in entry['analyses']:
                    if query.lower() in analysis.lower():
                        results.append(entry)
                        break
            # 向后兼容：检查旧格式的分析结果
            elif 'analysis' in entry and query.lower() in entry['analysis'].lower():
                results.append(entry)
        return results

def main():
    recorder = ScreenRecorder()
    player = VideoPlayer()
    
    try:
        while True:
            print("\n=== 录屏系统 ===")
            print("1. 开始录制")
            print("2. 搜索录制内容")
            print("3. 播放录制")
            print("4. 退出")
            
            choice = input("请选择操作 (1-4): ")
            
            if choice == '1':
                try:
                    duration = input("请输入录制时长（秒），直接回车表示无限制: ")
                    duration = int(duration) if duration.strip() else None
                    recorder.record_and_analyze(duration)
                except ValueError:
                    print("无效的时长输入，请重试")
            elif choice == '2':
                query = input("请输入搜索关键词: ")
                results = recorder.search_recordings(query)
                if results:
                    print("\n搜索结果:")
                    for result in results:
                        print(f"\n时间: {result['timestamp']}")
                        print(f"视频文件: {result['video_file']}")
                        if 'analyses' in result:
                            print("关键帧分析结果:")
                            for i, analysis in enumerate(result['analyses'], 1):
                                print(f"\n关键帧 {i}:")
                                print(analysis)
                        elif 'analysis' in result:
                            print("分析结果:")
                            print(result['analysis'])
                else:
                    print("未找到匹配的结果")
            elif choice == '3':
                player.main()
            elif choice == '4':
                print("退出程序")
                break
            else:
                print("无效的选择，请重试")
                
    except KeyboardInterrupt:
        print("\n程序已终止")
        if recorder.is_recording:
            recorder.stop_recording()
            if recorder.current_video_file:
                recorder.process_recording(recorder.current_video_file)

if __name__ == "__main__":
    main() 