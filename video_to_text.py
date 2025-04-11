import os
import time
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from pydub import AudioSegment

def extract_audio(video_path, audio_path):
    """비디오 또는 오디오 파일에서 오디오 추출"""
    # 파일 확장자 확인
    file_ext = os.path.splitext(video_path)[1].lower()
    
    if file_ext in ['.mp4', '.mov', '.avi', '.mkv']:  # 비디오 파일인 경우
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
    elif file_ext in ['.m4a', '.mp3', '.wav']:  # 오디오 파일인 경우
        # 오디오 파일을 그대로 복사
        audio = AudioSegment.from_file(video_path)
        audio.export(audio_path, format="mp3")
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {file_ext}")

def transcribe_audio(audio_path, max_retries=3):
    """오디오를 텍스트로 변환"""
    recognizer = sr.Recognizer()
    
    # 오디오 파일을 WAV 형식으로 변환
    audio = AudioSegment.from_file(audio_path)
    audio.export("temp.wav", format="wav")
    
    # 오디오 파일을 더 작은 청크로 나누기
    chunk_length = 30000  # 30초
    chunks = []
    
    for i in range(0, len(audio), chunk_length):
        chunk = audio[i:i + chunk_length]
        chunk.export(f"temp_chunk_{i}.wav", format="wav")
        chunks.append(f"temp_chunk_{i}.wav")
    
    full_text = []
    
    for chunk_file in chunks:
        for attempt in range(max_retries):
            try:
                with sr.AudioFile(chunk_file) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data, language='ko-KR')
                    full_text.append(text)
                    print(f"청크 {chunk_file} 성공적으로 변환됨 (시도 {attempt + 1}/{max_retries})")
                    break
            except sr.RequestError:
                if attempt < max_retries - 1:
                    print(f"청크 {chunk_file} 처리 중 오류 발생. 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(2)  # 잠시 대기 후 재시도
                    continue
                else:
                    print(f"청크 {chunk_file} 처리 중 오류 발생 (최대 재시도 횟수 도달)")
            except sr.UnknownValueError:
                if attempt < max_retries - 1:
                    print(f"청크 {chunk_file}에서 음성을 인식할 수 없습니다. 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(2)  # 잠시 대기 후 재시도
                    continue
                else:
                    print(f"청크 {chunk_file}에서 음성을 인식할 수 없습니다 (최대 재시도 횟수 도달)")
    
    # 임시 파일들 정리
    os.remove("temp.wav")
    for chunk_file in chunks:
        if os.path.exists(chunk_file):
            os.remove(chunk_file)
    
    return " ".join(full_text)

def process_video(video_path):
    """비디오 또는 오디오 파일 처리 메인 함수"""
    # 파일 이름에서 확장자를 제외한 부분 추출
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 임시 오디오 파일 경로
    audio_path = f"temp_audio_{base_name}.mp3"
    
    try:
        # 비디오/오디오에서 오디오 추출
        print(f"\n[{base_name}] 오디오 추출 중...")
        extract_audio(video_path, audio_path)
        
        # 오디오를 텍스트로 변환
        print(f"[{base_name}] 텍스트 변환 중...")
        text = transcribe_audio(audio_path)
        
        # 프롬프트 템플릿
        prompt_template = """아래 강의 텍스트는 음성 강의를 그대로 텍스트로 변환한 것입니다.
이 텍스트의 내용을 최대한 빠짐없이 요약 정리해주세요.
논리 흐름에 따라 적절히 단락을 나누고, 중요한 개념, 정의, 예시, 설명 등을 포함해
교재 수준의 필기 형태로 정리해주세요

조건:
- 단순 요약이 아닌, 내용을 충실히 재구성한 형태로
- 빠진 내용 없이 핵심을 유지하면서
- 가능한 용어나 개념은 명확하게 정리
- 강의의 전체 흐름이 보이게 구조화

텍스트 :
"""
        
        # 결과 저장
        with open(f"lecture_text_{base_name}.txt", "w", encoding="utf-8") as f:
            f.write(prompt_template + text)
        print(f"[{base_name}] 변환된 텍스트가 lecture_text_{base_name}.txt 파일에 저장되었습니다.")
        
    finally:
        # 임시 파일 정리
        if os.path.exists(audio_path):
            os.remove(audio_path)

def process_multiple_videos():
    """여러 비디오 파일을 처리하는 함수"""
    print("처리할 비디오 파일들의 경로를 입력하세요 (입력이 끝나면 빈 줄을 입력하세요):")
    video_paths = []
    
    while True:
        path = input().strip()
        if not path:  # 빈 줄이 입력되면 종료
            break
        video_paths.append(path)
    
    if not video_paths:
        print("처리할 파일이 입력되지 않았습니다.")
        return
    
    print(f"\n총 {len(video_paths)}개의 파일을 처리합니다...")
    
    for i, video_path in enumerate(video_paths, 1):
        print(f"\n[{i}/{len(video_paths)}] 처리 중...")
        process_video(video_path)
    
    print("\n모든 파일 처리가 완료되었습니다!")

if __name__ == "__main__":
    process_multiple_videos() 