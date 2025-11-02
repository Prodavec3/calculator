import pandas as pd
import io
from models.room import Room

def export_calculation_results_to_excel(
    room_data,
    structural_results=None,
    combined_results=None,
    structural_materials=None,
    acoustic_materials=None
):
    """
    Экспорт данных расчета реверберации помещения в Excel.
    Возвращает объект BytesIO, готовый для скачивания в Streamlit.
    """

    output = io.BytesIO()

    # Создаем Excel через pandas
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

            # --------------------------
            # 1. Исходные данные
            # --------------------------
            input_rows = []

            input_rows.append(["Наименование помещения", room_data.get('name', '')])
            input_rows.append(["Назначение помещения", room_data.get('purpose', '')])
            input_rows.append(["Длина (м)", room_data.get('length', '')])
            input_rows.append(["Ширина (м)", room_data.get('width', '')])
            input_rows.append(["Высота (м)", room_data.get('height', '')])
            input_rows.append(["Объем (м³)", room_data.get('volume', '')])
            input_rows.append(["Общая площадь поверхностей (м²)", room_data.get('total_surface_area', '')])

            # Добавляем материалы
            if structural_materials:
                input_rows.append([])
                input_rows.append(["Ограждающие конструкции"])
                input_rows.append(["№", "Поверхность", "Материал", "Площадь (м²)"])
                for i, mat in enumerate(structural_materials):
                    input_rows.append([i+1, mat.get('surface_type',''), mat.get('name',''), mat.get('area','')])

            if acoustic_materials:
                input_rows.append([])
                input_rows.append(["Акустические материалы"])
                input_rows.append(["№", "Поверхность", "Материал", "Площадь (м²)"])
                for i, mat in enumerate(acoustic_materials):
                    input_rows.append([i+1, mat.get('surface_type',''), mat.get('name',''), mat.get('area','')])

            df_input = pd.DataFrame(input_rows)
            df_input.to_excel(writer, sheet_name='Исходные данные', index=False, header=False)

            # --------------------------
            # 2. Расчет ОК
            # --------------------------
            if structural_results:
                _create_results_sheet(writer, structural_results, 'Расчет ОК')

            # --------------------------
            # 3. Расчет с АК
            # --------------------------
            if combined_results:
                _create_results_sheet(writer, combined_results, 'Расчет с АК')

             #--------------------------
             #4. Сравнение
            # --------------------------
            if structural_results and combined_results:
                _create_chart_data_sheet(writer, room_data, structural_results, combined_results)
             
            output.seek(0)
            return output

    except Exception as e:
        raise RuntimeError(f"Ошибка при формировании Excel файла: {e}")


# --------------------------
# Вспомогательные функции
# --------------------------
def _create_results_sheet(writer, results, sheet_name):
    """
    Создание листа с расчетами реверберации.
    """
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    rows = []

    for freq in frequencies:
        try:
            rt = results.get('reverberation_times', {}).get(freq, None)
            avg_alpha = results.get('average_absorption_coefficients', {}).get(freq, None)
            eq_area = results.get('equivalent_absorption_areas', {}).get(freq, None)
            phi = results.get('phi_values', {}).get(freq, None)

            row = {
                'Частота (Гц)': freq,
                'Время реверберации (с)': rt,
                'Средний КЗП': avg_alpha,
                'ЭПЗ общая (м²)': eq_area,
                'φ(αср)': phi
            }
# Если есть структурные и акустические ЭПЗ
            if 'structural_absorption_areas' in results:
                row['ЭПЗ ОК (м²)'] = results.get('structural_absorption_areas', {}).get(freq, None)
                row['ЭПЗ АК (м²)'] = results.get('acoustic_absorption_areas', {}).get(freq, None)

            rows.append(row)
        except Exception:
            continue  # пропускаем частоту при проблеме

    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
def _create_chart_data_sheet(writer, room_data, structural_results, combined_results):
    """
    Создание листа с данными для построения графиков времени реверберации.
    """
    from data.reverberation_standarts import REVERBERATION_STANDARDS
        
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    purpose = room_data.get("purpose", "")
    
    min_times = []
    max_times = []
    structural_times = []
    combined_times = []
    
    for f in frequencies:
        min_times.append(REVERBERATION_STANDARDS.get(purpose, {}).get("min", {}).get(f, None))
        max_times.append(REVERBERATION_STANDARDS.get(purpose, {}).get("max", {}).get(f, None))
        structural_times.append(structural_results['reverberation_times'].get(f, None))
        if combined_results:
            combined_times.append(combined_results['reverberation_times'].get(f, None))
        else:
            combined_times.append(None)
    
    rows = [["Частота (Гц)", "Мин. время", "Макс. время", "Исходное время (ОК)", "Итоговое время (с АК)"]]
    for i, f in enumerate(frequencies):
        rows.append([f, min_times[i], max_times[i], structural_times[i], combined_times[i]])
    
    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name="Графики", index=False, header=False)

