#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Apache 라이선스 버전 2.0 ( "라이선스")에 따라 사용이 허가되었습니다.
# 라이선스를 준수하는 경우를 제외하고는이 파일을 사용할 수 없습니다.
# 라이센스 사본은
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# 관련 법률에서 요구하거나 서면으로 동의하지 않는 한, 소프트웨어
# 라이선스에 따라 배포되는 것은 "있는 그대로"배포됩니다.
# 명시 적이든 묵시적이든 어떠한 종류의 보증이나 조건없이.
# 권한을 관리하는 특정 언어에 대해서는 라이선스를 참조하십시오.
# 라이선스에 따른 제한.
"""
스트리밍 API를 사용하는 Google Cloud Speech API 샘플 애플리케이션입니다.
참고 :이 모듈에는 추가 종속성 'pyaudio'가 필요합니다. 설치하기 위해서
pip 사용 :
     pip 설치 pyaudio
사용 예 :
     파이썬 transcribe_streaming_mic.py
"""
# 음성 스크립트 스트리밍 마이크 시작
from __future__ import division

import re
import sys
import librosa
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import numpy as np
import pyaudio
from six.moves import queue

# 오디오 녹음 매개 변수
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """오디오 청크를 생성하는 생성기로 녹음 스트림을 엽니다.."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # 오디오 데이터의 스레드로부터 안전한 버퍼 생성
        self._buff = queue.Queue()
        self.closed = True

    # with 구문에 진입하는 시점에 자동으로 호출되는 메소드
    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # API는 현재 1 채널 (모노) 오디오 만 지원합니다.
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # 버퍼 객체를 채우기 위해 오디오 스트림을 비동기 적으로 실행합니다.
            # 입력 장치의 버퍼가
            # 호출 스레드가 네트워크 요청 등을하는 동안 오버플로
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self
    # with구문을 빠져나오기 직전에 호출되는 메소드 type, value, traceback는 with문을 빠져나오기 전에 예외가 발생했을 때의 정보를 나타냄
    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # 제너레이터에게 종료 신호를 보내 클라이언트가
        # streaming_recognize 메서드는 프로세스 종료를 차단하지 않습니다.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """오디오 스트림에서 버퍼로 데이터를 지속적으로 수집합니다."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # 블로킹 get ()을 사용하여 적어도 하나의 청크가 있는지 확인하십시오.
            # 데이터, 청크가 None이면 반복을 중지합니다.
            # 오디오 스트림의 끝.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # 이제 여전히 버퍼링 된 다른 데이터를 소비합니다.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses):
    """
        서버 응답을 반복하고 인쇄합니다.
         전달 된 응답은 응답이 발생할 때까지 차단되는 생성기입니다.
         서버에서 제공합니다.
         각 응답에는 여러 결과가 포함될 수 있으며 각 결과에는
         여러 대안; 자세한 내용은 https://goo.gl/tjCPAU를 참조하세요. 여기 우리
         상위 결과의 상위 대안에 대한 트랜스 크립 션 만 인쇄합니다.
         이 경우 중간 결과에 대한 응답도 제공됩니다. 만약
         응답은 중간 응답입니다. 마지막에 줄 바꿈을 인쇄하여
         응답이 최종 결과가 될 때까지 덮어 쓸 다음 결과. 에 대한
         마지막으로, 최종 전사를 보존하기 위해 개행을 인쇄하십시오.
     """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # `results` 목록은 연속적입니다. 스트리밍의 경우 우리는
        # 고려되는 첫 번째 결과, 일단`is_final`이되면
        # 다음 발화 고려로 이동합니다.
        result = response.results[0]
        if not result.alternatives:
            continue

        # 상위 대안의 필사본을 표시합니다.
        transcript = result.alternatives[0].transcript

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=2)

        data = np.fromstring(stream.read(CHUNK), dtype=np.int16)

        p.terminate()
        # 중간 결과를 표시하지만 끝에 캐리지 리턴이 있습니다.
        # 줄이므로 다음 줄이 덮어 씁니다.
        # 이전 결과가이 결과보다 길면 인쇄해야합니다.
        # 이전 결과를 덮어 쓸 추가 공백
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)
            print(int(np.average(np.abs(data))))
            stream.stop_stream()
            stream.close()

            # 전사 된 문구 중 하나라도
            # 키워드 중 하나.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0


def main():
    # http://g.co/cloud/speech/docs/languages 참조
    # 지원되는언어 목록은
    language_code = 'ko-KR'  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # 이제 트랜스 크립 션 응답을 사용합니다.
        listen_print_loop(responses)


if __name__ == '__main__':
    main()
# END 음성 스크립트 스트리밍 마이크