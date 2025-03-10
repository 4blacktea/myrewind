import os
import subprocess
from datetime import datetime

class KeyframeAnalyzer:
    def __init__(self, keyframes_dir="keyframes"):
        self.keyframes_dir = keyframes_dir
        self.ensure_directory()

    def ensure_directory(self):
        """确保关键帧目录存在"""
        os.makedirs(self.keyframes_dir, exist_ok=True)

    def extract_keyframes(self, video_file):
        """从视频中提取关键帧"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keyframe_files = []
        
        try:
            # 使用ffmpeg提取所有关键帧
            command = [
                'ffmpeg', '-i', video_file,
                '-vf', 'select=eq(pict_type\,I)',
                '-vsync', 'vfr',  # 使用可变帧率
                '-frame_pts', '1',  # 在文件名中包含时间戳
                '-y',
                os.path.join(self.keyframes_dir, f'keyframe_{timestamp}_%d.jpg')
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"提取关键帧出错: {result.stderr}")
                return None
            
            # 获取所有生成的关键帧文件
            for file in os.listdir(self.keyframes_dir):
                if file.startswith(f'keyframe_{timestamp}_') and file.endswith('.jpg'):
                    keyframe_files.append(os.path.join(self.keyframes_dir, file))
            
            return keyframe_files
        except Exception as e:
            print(f"提取关键帧出错: {str(e)}")
            return None

    def analyze_image(self, image_path):
        """使用Ollama分析图片"""
        try:
            # 使用绝对路径
            abs_image_path = os.path.abspath(image_path)
            print(f"正在分析图片: {abs_image_path}")
            
            # 检查文件是否存在
            if not os.path.exists(abs_image_path):
                print(f"错误: 图片文件不存在: {abs_image_path}")
                return None
                
            # 检查文件大小
            file_size = os.path.getsize(abs_image_path)
            print(f"图片大小: {file_size} 字节")
            
            # 使用命令行方式调用Ollama
            command = [
                'ollama', 'run', 'minicpm-v:latest',
                f'简要介绍图片 {abs_image_path}'
            ]
            print(f"执行命令: {' '.join(command)}")
            
            result = subprocess.run(command, capture_output=True, text=True)
            print(f"命令返回码: {result.returncode}")
            
            if result.returncode == 0:
                # 移除 "Added image" 行，只返回实际的描述
                response = result.stdout.strip()
                if "Added image" in response:
                    response = response.split("\n", 1)[1].strip()
                print(f"分析结果: {response}")
                return response
            else:
                print(f"分析图片出错: {result.stderr}")
                return None
        except Exception as e:
            print(f"分析图片出错: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return None

    def process_video(self, video_file):
        """处理视频文件，提取关键帧并分析"""
        print("正在提取关键帧...")
        keyframe_files = self.extract_keyframes(video_file)
        if not keyframe_files:
            return None, None

        print("正在分析关键帧...")
        analyses = []
        for keyframe_file in keyframe_files:
            analysis = self.analyze_image(keyframe_file)
            if analysis:
                analyses.append(analysis)

        return keyframe_files, analyses 