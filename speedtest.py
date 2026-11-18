#!/usr/bin/env python3
"""
Тест скорости скачивания: выполняет N последовательных полных скачиваний URL
и печатает среднее время запроса, суммарный объём и скорость.
"""

from __future__ import annotations

import argparse
import http.client
import sys
import time
import urllib.error
import urllib.request
from statistics import mean

CHUNK_SIZE = 64 * 1024          # 64 КиБ — размер читаемого чанка
USER_AGENT = "internet-speed-test/1.0"


def download_once(url: str, timeout: float) -> tuple[int, float]:
    """Скачивает url полностью. Возвращает (получено_байт, время_в_секундах)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    start = time.perf_counter()
    bytes_received = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            bytes_received += len(chunk)
    elapsed = time.perf_counter() - start
    return bytes_received, elapsed


def run(url: str, count: int, timeout: float) -> int:
    print(f"Целевой URL: {url}")
    print(f"Запросов:    {count}")
    print(f"Таймаут:     {timeout} с\n")

    total_bytes = 0
    timings: list[float] = []
    failures = 0

    for i in range(1, count + 1):
        try:
            size, elapsed = download_once(url, timeout)
        except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
            failures += 1
            print(f"[{i:>2}/{count}] ОШИБКА: {exc}")
            continue

        total_bytes += size
        timings.append(elapsed)
        # скорость одного запроса в Кбит/с (десятичные: 1 Кбит = 1000 бит)
        per_req_kbps = (size * 8 / 1000) / elapsed if elapsed > 0 else 0.0
        print(
            f"[{i:>2}/{count}] {size:>10} байт  "
            f"{elapsed:6.3f} с  {per_req_kbps:10.2f} Кбит/с"
        )

    if not timings:
        print("\nВсе запросы завершились ошибкой.", file=sys.stderr)
        return 1

    total_time = sum(timings)
    avg_time = mean(timings)
    avg_bytes_per_sec = total_bytes / total_time if total_time > 0 else 0.0
    avg_kbps = avg_bytes_per_sec * 8 / 1000
    avg_mbps = avg_bytes_per_sec * 8 / 1_000_000

    print("\n--- Итог ---")
    print(f"Успешных запросов:     {len(timings)}/{count}"
          + (f"  (с ошибкой: {failures})" if failures else ""))
    print(f"Среднее время запроса: {avg_time:.3f} с")
    print(f"Всего скачано:         {total_bytes} байт "
          f"({total_bytes / 1_000_000:.2f} МБ)")
    print(f"Скорость скачивания:   {avg_kbps:.2f} Кбит/с "
          f"({avg_mbps:.3f} Мбит/с)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Замер скорости скачивания: последовательно скачивает URL N раз."
    )
    parser.add_argument("url", help="URL для скачивания (например, тяжёлая картинка)")
    parser.add_argument("-n", "--count", type=int, default=10,
                        help="Количество последовательных запросов (по умолчанию: 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30.0,
                        help="Таймаут на один запрос в секундах (по умолчанию: 30)")
    args = parser.parse_args()
    return run(args.url, args.count, args.timeout)


if __name__ == "__main__":
    sys.exit(main())