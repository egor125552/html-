import pandas as pd
import numpy as np
import re
import os
import time
import logging
from manual_matching_dictionary import manual_matching_dictionary # ИМПОРТИРУЕМ СЛОВАРЬ

# ================== НАСТРОЙКИ ЛОГИРОВАНИЯ ==================
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("merger.log", mode='w', encoding='utf-8'),
                        logging.StreamHandler()
                    ])

# ================== СЛОВАРИ И КОНСТАНТЫ ==================

# Используем импортированный словарь
MANUAL_MATCH_DICT = manual_matching_dictionary

def clean_key(text):
    """Более надежная очистка ключей для сопоставления."""
    if not isinstance(text, str): return ""
    text = text.lower()
    # Заменяем знаки препинания, которые могут мешать, на пробел
    text = re.sub(r'[,\."\'`’“”()\[\]]', ' ', text)
    # Заменяем множественные пробелы на один
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --- Функции для загрузки и обработки данных ---

def load_main_data(filepath):
    """
    Загружает основной файл, обрабатывает двухуровневый заголовок и находит столбец с товарами.
    """
    logging.info(f"Загрузка основного файла: {filepath}...")
    if not os.path.exists(filepath):
        logging.error(f"Основной файл не найден по пути: {filepath}")
        return None, None, None

    try:
        df = pd.read_excel(filepath, header=[0, 1])
        original_columns = df.columns
        work_df = df.copy()
        # Создаем плоские, рабочие названия колонок
        work_df.columns = ['_'.join(map(str, col)).strip().replace('Unnamed: ', '').replace('_level_0', '') for col in work_df.columns.values]

        product_column = None
        for col in work_df.columns:
            # Ищем столбец, который содержит 'номенклатура', но не является просто заголовком группы
            if 'номенклатура' in col.lower() and not col.lower().endswith('_номенклатура'):
                 product_column = col
                 break

        # Если не нашли по точному совпадению, ищем по частичному
        if not product_column:
            for col in work_df.columns:
                 if 'номенклатура' in col.lower():
                    product_column = col
                    break

        if product_column:
            logging.info(f"Столбец с наименованиями определен как: '{product_column}'")
        else:
            logging.error("Не удалось найти столбец со словом 'номенклатура' в заголовке.")
            return None, None, None

        return work_df, product_column, original_columns
    except Exception as e:
        logging.critical(f"Критическая ошибка при чтении основного файла: {e}")
        return None, None, None

def load_catalogs(filepaths):
    """
    Загружает, объединяет и очищает файлы-каталоги.
    """
    logging.info("Загрузка и объединение файлов-каталогов...")
    all_catalogs = []
    for path in filepaths:
        if os.path.exists(path):
            try:
                # Указываем openpyxl, чтобы избежать предупреждений о стилях
                all_catalogs.append(pd.read_excel(path, engine='openpyxl'))
                logging.info(f" - Каталог '{path}' успешно загружен.")
            except Exception as e:
                logging.warning(f" - Не удалось прочитать каталог '{path}'. Ошибка: {e}")
        else:
            logging.warning(f" - Файл каталога не найден: '{path}', пропускаем.")

    if not all_catalogs:
        logging.error("Не найдено ни одного файла-каталога.")
        return None

    master_catalog = pd.concat(all_catalogs, ignore_index=True)
    logging.info(f"Всего позиций в каталогах до очистки: {len(master_catalog)}")
    master_catalog.dropna(subset=['Название', 'URL Картинки в S3'], inplace=True)
    logging.info(f"Всего позиций в каталогах после очистки: {len(master_catalog)}")

    return master_catalog

def main():
    """
    Основная функция выполнения скрипта.
    """
    main_file = 'Движение товара.xlsx'
    catalog_files = [f'products_garfield_{i}.xlsx' for i in range(1, 4)]

    df_main, product_column_name, original_columns = load_main_data(main_file)
    if df_main is None:
        logging.error("Выполнение скрипта прервано из-за ошибки при загрузке основного файла.")
        return

    df_catalog = load_catalogs(catalog_files)
    if df_catalog is None:
        logging.error("Выполнение скрипта прервано из-за ошибки при загрузке каталогов.")
        generate_output_files(df_main, None, set(), product_column_name, original_columns)
        return

    logging.info("Этап загрузки и предобработки данных завершен.")

    df_main['matched_url'] = pd.NA
    used_catalog_indices = set()

    logging.info("Начинается этап ручного сопоставления по словарю...")
    manual_matches = 0
    catalog_url_map = df_catalog.set_index('Название')['URL Картинки в S3'].to_dict()

    logging.info("Очистка ключей словаря для ручного сопоставления...")
    CLEANED_MANUAL_MATCH_DICT = {clean_key(k): v for k, v in MANUAL_MATCH_DICT.items() if k}
    logging.info(f"Очистка ключей завершена. Размер словаря: {len(CLEANED_MANUAL_MATCH_DICT)}.")

    for index, row in df_main.iterrows():
        original_name = row[product_column_name]
        if not isinstance(original_name, str) or not original_name.strip():
            continue
        cleaned_name = clean_key(original_name)

        if cleaned_name in CLEANED_MANUAL_MATCH_DICT:
            catalog_name = CLEANED_MANUAL_MATCH_DICT[cleaned_name]
            if catalog_name in catalog_url_map:
                df_main.loc[index, 'matched_url'] = catalog_url_map[catalog_name]
                manual_matches += 1
                catalog_match_indices = df_catalog.index[df_catalog['Название'] == catalog_name].tolist()
                if catalog_match_indices:
                    used_catalog_indices.add(catalog_match_indices[0])

    logging.info(f"Выполнено {manual_matches} сопоставлений по ручному словарю.")

    total_matched = df_main['matched_url'].notna().sum()
    total_unmatched = len(df_main) - total_matched
    logging.info("\n" + "="*15 + " ИТОГОВЫЙ ОТЧЕТ " + "="*15)
    logging.info(f"Всего обработано строк: {len(df_main)}")
    logging.info(f"ИТОГО найдено совпадений: {total_matched}")
    logging.info(f"Осталось без совпадений: {total_unmatched}")
    logging.info("="*48)

    logging.info("Начинается этап генерации выходных файлов...")
    generate_output_files(df_main, df_catalog, used_catalog_indices, product_column_name, original_columns)

def generate_output_files(df_main, df_catalog, used_catalog_indices, product_column_name, original_columns):
    """
    Создает итоговый Excel-файл и текстовый отчет для отладки.
    """
    output_excel_path = 'output_with_url.xlsx'
    logging.info(f"Сохранение основного файла с результатами в '{output_excel_path}'...")

    # Создаем копию для сохранения и переименовываем колонку
    df_to_save = df_main.copy()
    df_to_save.rename(columns={'matched_url': 'URL'}, inplace=True)

    try:
        with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
            df_to_save.to_excel(writer, index=False, sheet_name='Sheet1')
            workbook  = writer.book
            worksheet = writer.sheets['Sheet1']

            # Авто-подбор ширины колонок
            for i, col in enumerate(df_to_save.columns):
                # Находим максимальную длину значения в колонке
                max_len = df_to_save[col].astype(str).map(len).max()
                if pd.isna(max_len):
                    max_len = 0
                # Сравниваем с длиной заголовка и берем большее значение
                column_width = max(int(max_len), len(str(col)))
                # Устанавливаем ширину с небольшим запасом
                worksheet.set_column(i, i, column_width + 2)

        logging.info(f"Файл '{output_excel_path}' успешно создан.")
    except Exception as e:
        logging.error(f"Не удалось сохранить Excel-файл. Ошибка: {e}")

    debug_report_path = 'debug_report.txt'
    logging.info(f"Создание отладочного отчета '{debug_report_path}'...")
    try:
        with open(debug_report_path, 'w', encoding='utf-8') as f:
            f.write("="*30 + "\nСЕКЦИЯ 1: ТОВАРЫ БЕЗ СОВПАДЕНИЙ\n" + "="*30 + "\n")
            unmatched_products = df_main[df_main['matched_url'].isna()]
            if not unmatched_products.empty:
                for index, row in unmatched_products.iterrows():
                    # Убедимся, что product_column_name существует в row
                    if product_column_name in row:
                        f.write(f"Строка #{index + 2}: {row[product_column_name]}\n")
            else:
                f.write("Все товары из основного файла были успешно сопоставлены.\n")

            f.write("\n\n" + "="*30 + "\nСЕКЦИЯ 2: НЕИСПОЛЬЗОВАННЫЕ ТОВАРЫ ИЗ КАТАЛОГОВ\n" + "="*30 + "\n")
            if df_catalog is not None and not df_catalog.empty:
                all_catalog_indices = set(df_catalog.index)
                unused_indices = all_catalog_indices - used_catalog_indices
                if unused_indices:
                    unused_catalog_items = df_catalog.loc[list(unused_indices)]
                    for index, row in unused_catalog_items.iterrows():
                        f.write(f"{row['Название']}\n")
                else:
                    f.write("Все товары из каталогов были использованы хотя бы один раз.\n")
            else:
                f.write("Каталоги не были загружены или пусты.\n")

        logging.info(f"Отчет '{debug_report_path}' успешно создан.")
    except Exception as e:
        logging.error(f"Не удалось создать отладочный отчет. {e}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    logging.info(f"Скрипт завершил работу за {end_time - start_time:.2f} секунд.")