"""
Модуль для обработки команд пользователя.
"""

import services
from database import database


PATH_FOR_FILES = 'temp/'


def parse_command(command: list[str]) -> str | tuple:
    """
    Обрабатывает команды пользователя и возвращает результат:
    строку с ответом, кортеж ('send_file', <название файла>)
    или кортеж ('unknown command', ).

    :param command: Команда пользователя.
    :return: Строка или кортеж.
    """
    if len(command) == 1:
        cmd = command[0].lower()
        db_info = ()
        if cmd == 'жк':
            db_info = database.get_one_field_info('projects', 'name')
        elif cmd == 'город':
            db_info = database.get_one_field_info('projects', 'city')
        elif cmd == 'метро':
            db_info = database.get_one_field_info('projects', 'metro')
        answer = '\n'.join(str(tup[0]) for tup in db_info)
        answer += f"\n\nВсего {len(db_info)}."
        return answer

    elif len(command) == 2:
        if command[0].lower() == 'квартира':
            db_info = database.get_flat(int(command[1]))
            if len(db_info) > 0:
                file_name = f'{PATH_FOR_FILES}Квартира_id{int(command[1])}__{services.get_data_time()}'
                services.save_to_excel_file(db_info, file_name)
                return 'send_file', file_name
            else:
                return f'Квартира с id {command[1]} не найдена.'

    elif len(command) == 8 and command[0].lower() == "квартиры":
        keys = database.flats_filter.keys()
        command[5] = command[5] + '-__-__'      # приводит дату к виду '2024-__-__'
        flats_filter = dict(zip(keys, command[1:]))
        print(f"{flats_filter=}")
        db_info = database.get_flats_by_filter_last_price(flats_filter)
        if len(db_info) > 0:
            file_name = f'{PATH_FOR_FILES}Квартиры__{services.get_data_time()}'
            services.save_to_excel_file(db_info, file_name)
            return 'send_file', file_name
        else:
            return f'Квартиры по указанному фильтру не найдены.'
    else:
        return 'unknown command',
