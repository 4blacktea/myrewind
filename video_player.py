import os
import subprocess
import json
from datetime import datetime
import ffmpeg

class VideoPlayer:
    def __init__(self, recordings_dir="recordings", metadata_file="recording_metadata.json"):
        self.recordings_dir = recordings_dir
        self.metadata_file = metadata_file
        self.metadata = self.load_metadata()
        self.current_process = None

    def load_metadata(self):
        """加载录制元数据"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def list_recordings(self):
        """列出所有可用的录制"""
        if not self.metadata:
            print("没有找到任何录制")
            return []
        
        print("\n可用的录制:")
        for i, entry in enumerate(self.metadata, 1):
            print(f"\n{i}. 时间: {entry['timestamp']}")
            print(f"   视频文件: {entry['video_file']}")
            if 'analyses' in entry:
                print(f"   关键帧数量: {len(entry['analyses'])}")
        return self.metadata

    def play_recording(self, video_file, start_time=None, duration=None):
        """播放录制的视频"""
        if not os.path.exists(video_file):
            print(f"错误: 找不到视频文件 {video_file}")
            return

        command = ['ffplay', '-autoexit']
        
        if start_time is not None:
            command.extend(['-ss', str(start_time)])
        if duration is not None:
            command.extend(['-t', str(duration)])
            
        command.append(video_file)
        
        try:
            self.current_process = subprocess.Popen(command)
            self.current_process.wait()
            self.current_process = None
        except KeyboardInterrupt:
            if self.current_process:
                self.current_process.terminate()
                self.current_process = None
            print("\n播放已停止")

    def get_video_info(self, video_file):
        """获取视频信息"""
        try:
            probe = ffmpeg.probe(video_file)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            return {
                'duration': float(probe['format']['duration']),
                'width': int(video_info['width']),
                'height': int(video_info['height']),
                'fps': eval(video_info['r_frame_rate'])
            }
        except Exception as e:
            print(f"获取视频信息出错: {str(e)}")
            return None

    def segment_video(self, video_file, segment_duration=60):
        """将视频分割成指定时长的片段"""
        if not os.path.exists(video_file):
            print(f"错误: 找不到视频文件 {video_file}")
            return []

        video_info = self.get_video_info(video_file)
        if not video_info:
            return []

        total_duration = video_info['duration']
        segments = []
        current_time = 0

        while current_time < total_duration:
            segment_end = min(current_time + segment_duration, total_duration)
            segments.append((current_time, segment_end))
            current_time = segment_end

        return segments

    def play_segment(self, video_file, start_time, duration):
        """播放视频的特定片段"""
        print(f"\n播放片段: {start_time:.1f}s - {start_time + duration:.1f}s")
        self.play_recording(video_file, start_time, duration)

def main():
    player = VideoPlayer()
    
    while True:
        print("\n=== 视频播放器 ===")
        print("1. 列出所有录制")
        print("2. 播放完整视频")
        print("3. 播放视频片段")
        print("4. 退出")
        
        choice = input("请选择操作 (1-4): ")
        
        if choice == '1':
            player.list_recordings()
            
        elif choice == '2':
            recordings = player.list_recordings()
            if not recordings:
                continue
                
            try:
                index = int(input("请输入要播放的视频编号: ")) - 1
                if 0 <= index < len(recordings):
                    video_file = recordings[index]['video_file']
                    player.play_recording(video_file)
                else:
                    print("无效的视频编号")
            except ValueError:
                print("请输入有效的数字")
                
        elif choice == '3':
            recordings = player.list_recordings()
            if not recordings:
                continue
                
            try:
                index = int(input("请输入要播放的视频编号: ")) - 1
                if 0 <= index < len(recordings):
                    video_file = recordings[index]['video_file']
                    segments = player.segment_video(video_file)
                    
                    if segments:
                        print("\n可用的片段:")
                        for i, (start, end) in enumerate(segments, 1):
                            print(f"{i}. {start:.1f}s - {end:.1f}s")
                            
                        segment_index = int(input("请输入要播放的片段编号: ")) - 1
                        if 0 <= segment_index < len(segments):
                            start_time, end_time = segments[segment_index]
                            duration = end_time - start_time
                            player.play_segment(video_file, start_time, duration)
                        else:
                            print("无效的片段编号")
                    else:
                        print("无法分割视频")
                else:
                    print("无效的视频编号")
            except ValueError:
                print("请输入有效的数字")
                
        elif choice == '4':
            print("退出程序")
            break
            
        else:
            print("无效的选择，请重试")

if __name__ == "__main__":
    main() 