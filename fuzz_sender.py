# ========== МОДУЛЬ ОТПРАВКИ PAYLOAD'ОВ (ЗАКОММЕНТИРОВАН) ==========
#
# import json
#
# def send_payloads_to_api(payloads, target_api, method='GET', field_name='user_id', timeout=5):
#     """
#     Отправляет сгенерированные payloads на целевой API для фаззинга.
#
#     Параметры:
#     -----------
#     payloads : list[str]
#         Список JSON-строк, сгенерированных моделью
#     target_api : str
#         URL целевого API (например, 'http://localhost:8080/api/test')
#     method : str
#         HTTP-метод: 'GET', 'POST', 'PUT', 'DELETE' (по умолчанию 'GET')
#     field_name : str
#         Имя поля в теле запроса для injection (по умолчанию 'user_id')
#     timeout : int
#         Таймаут ответа в секундах
#
#     Возвращает:
#     -----------
#     list[dict]
#         Список результатов с кодом ответа и временем отклика
#     """
#     import requests
#     from datetime import datetime
#
#     results = []
#     session = requests.Session()
#
#     for i, payload in enumerate(payloads):
#         try:
#             start_time = datetime.now()
#
#             # Распарсить payload как JSON
#             payload_obj = json.loads(payload)
#
#             # Отправить в зависимости от метода
#             if method.upper() == 'GET':
#                 # Отправить в query-параметрах
#                 response = session.get(
#                     target_api,
#                     params={field_name: payload_obj.get(field_name, payload)},
#                     timeout=timeout,
#                     verify=False
#                 )
#             elif method.upper() == 'POST':
#                 # Отправить в теле
#                 response = session.post(
#                     target_api,
#                     json={field_name: payload_obj.get(field_name, payload)},
#                     timeout=timeout,
#                     verify=False
#                 )
#             elif method.upper() == 'PUT':
#                 response = session.put(
#                     target_api,
#                     json={field_name: payload_obj.get(field_name, payload)},
#                     timeout=timeout,
#                     verify=False
#                 )
#             elif method.upper() == 'DELETE':
#                 response = session.delete(
#                     target_api,
#                     params={field_name: payload_obj.get(field_name, payload)},
#                     timeout=timeout,
#                     verify=False
#                 )
#             else:
#                 raise ValueError(f"Неизвестный метод: {method}")
#
#             elapsed = (datetime.now() - start_time).total_seconds()
#
#             result = {
#                 'index': i,
#                 'payload': payload[:100],
#                 'status_code': response.status_code,
#                 'response_time': elapsed,
#                 'success': response.status_code < 400,
#                 'error': None
#             }
#
#             # Попытка распарсить ответ как JSON
#             try:
#                 result['response_body'] = response.json()
#             except Exception:
#                 result['response_body'] = response.text[:200]
#
#             results.append(result)
#             print(f"[{i+1}/{len(payloads)}] {method.upper()} {target_api} -> {response.status_code} ({elapsed:.2f}s)")
#
#         except requests.exceptions.Timeout:
#             results.append({
#                 'index': i,
#                 'payload': payload[:100],
#                 'error': 'Таймаут ответа',
#                 'success': False
#             })
#             print(f"[{i+1}/{len(payloads)}] TIMEOUT")
#         except requests.exceptions.ConnectionError as e:
#             results.append({
#                 'index': i,
#                 'payload': payload[:100],
#                 'error': f'Ошибка подключения: {str(e)}',
#                 'success': False
#             })
#             print(f"[{i+1}/{len(payloads)}] CONNECTION ERROR")
#         except json.JSONDecodeError:
#             results.append({
#                 'index': i,
#                 'payload': payload[:100],
#                 'error': 'Невалидный JSON в payload',
#                 'success': False
#             })
#             print(f"[{i+1}/{len(payloads)}] INVALID JSON")
#         except Exception as e:
#             results.append({
#                 'index': i,
#                 'payload': payload[:100],
#                 'error': f'Ошибка: {str(e)}',
#                 'success': False
#             })
#             print(f"[{i+1}/{len(payloads)}] ERROR: {str(e)}")
#
#     session.close()
#     return results
#
#
# # ========== ПРИМЕР ИСПОЛЬЗОВАНИЯ ==========
# #
# # Чтобы использовать этот модуль, раскомментируйте и укажите реальный API:
# #
# # payloads = [...]  # Получить от /generate endpoint
# # results = send_payloads_to_api(
# #     payloads=payloads,
# #     target_api='http://target-api.com/endpoint',
# #     method='POST',
# #     field_name='user_id',
# #     timeout=10
# # )
# # for r in results:
# #     print(f"Payload {r['index']}: {r['status_code']} - {r.get('error', 'OK')}")
