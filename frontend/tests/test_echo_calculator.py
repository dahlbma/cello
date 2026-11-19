import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from frontend.echo_calculator import EchoSpotCalculator


class EchoSpotCalculatorLayoutTests(unittest.TestCase):
    def _write_order_file(
        self, path, compound_wells_by_layout, layout_names=None, order_count=None
    ):
        workbook = Workbook()
        order_sheet = workbook.active
        order_sheet.title = 'Compound list'
        order_sheet.append(['Compound Id', 'Batch Id', 'Final conc (nM)'])

        if order_count is None:
            order_count = sum(len(wells) for wells in compound_wells_by_layout)
        for index in range(1, order_count + 1):
            order_sheet.append([f'C{index:04d}', f'B{index:04d}', 1000])

        layout_sheet = workbook.create_sheet('Layout')
        for layout_index, compound_wells in enumerate(compound_wells_by_layout):
            header_row = 1 + (layout_index * 18)
            if layout_names:
                layout_sheet.cell(header_row, 1, layout_names[layout_index])
            for column in range(1, 25):
                layout_sheet.cell(header_row, column + 1, column)

            for row_index, row_name in enumerate('ABCDEFGHIJKLMNOP', 1):
                row_number = header_row + row_index
                layout_sheet.cell(row_number, 1, row_name)
                for column in range(1, 25):
                    layout_sheet.cell(row_number, column + 1, 'Empty')

            for well in compound_wells:
                row_name = well[0]
                column = int(well[1:])
                layout_sheet.cell(
                    header_row + 'ABCDEFGHIJKLMNOP'.index(row_name) + 1,
                    column + 1,
                ).value = None

        workbook.save(path)

    @staticmethod
    def _source_data(order_data):
        return [
            {
                'source_plate': 'PSOURCE1',
                'plate_subtype': '384LDV_DMSO',
                'source_well': 'A01',
                'compound_id': row['Compound Id'],
                'batch_id': str(row['Batch Id']),
                'source_conc_mm': 1.0,
            }
            for _, row in order_data.iterrows()
        ]

    def test_single_layout_is_repeated_for_each_destination_plate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / 'legacy.xlsx'
            output_path = Path(temp_dir) / 'echo.xlsx'
            self._write_order_file(
                input_path,
                [['A02', 'B01']],
                order_count=4,
            )

            calculator = EchoSpotCalculator()
            parsed_order, plate_layouts, is_multi_plate = (
                calculator.parse_excel_order_layouts(input_path)
            )
            self.assertFalse(is_multi_plate)
            self.assertEqual(len(plate_layouts), 1)

            _, special_wells, compound_wells = calculator.parse_excel_order(
                input_path
            )
            self.assertEqual(special_wells, [])
            self.assertEqual(compound_wells, ['A02', 'B01'])

            success = calculator.generate_echo_file(
                order_data=parsed_order,
                source_data=self._source_data(parsed_order),
                ctrl_plate='PCTRL01',
                dmso_plate='PDM001',
                diluent_vol_ul=100,
                destination_plates=['P100001', 'P100002'],
                excel_order_path=input_path,
                output_path=output_path,
            )

            self.assertTrue(success)
            output = pd.read_excel(output_path)
            self.assertEqual(
                output['Destination plate name'].tolist(),
                ['P100001', 'P100001', 'P100002', 'P100002'],
            )
            self.assertEqual(
                output['Destination well'].tolist(),
                ['A02', 'B01', 'A02', 'B01'],
            )

    def test_each_multi_plate_layout_is_used_in_sheet_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / 'multi.xlsx'
            output_path = Path(temp_dir) / 'echo.xlsx'
            self._write_order_file(
                input_path,
                [['A02', 'B01'], ['C03', 'D04']],
                ['P016-01', 'P016-02'],
            )

            calculator = EchoSpotCalculator()
            parsed_order, plate_layouts, is_multi_plate = (
                calculator.parse_excel_order_layouts(input_path)
            )
            self.assertTrue(is_multi_plate)
            self.assertEqual(
                [layout['compound_wells'] for layout in plate_layouts],
                [['A02', 'B01'], ['C03', 'D04']],
            )

            _, special_wells_by_plate, compound_wells_by_plate = (
                calculator.parse_excel_order(input_path)
            )
            self.assertEqual(special_wells_by_plate, [[], []])
            self.assertEqual(
                compound_wells_by_plate,
                [['A02', 'B01'], ['C03', 'D04']],
            )

            success = calculator.generate_echo_file(
                order_data=parsed_order,
                source_data=self._source_data(parsed_order),
                ctrl_plate='PCTRL01',
                dmso_plate='PDM001',
                diluent_vol_ul=100,
                destination_plates=['P200001', 'P200002'],
                excel_order_path=input_path,
                output_path=output_path,
            )

            self.assertTrue(success)
            output = pd.read_excel(output_path)
            self.assertEqual(
                output['Destination plate name'].tolist(),
                ['P200001', 'P200001', 'P200002', 'P200002'],
            )
            self.assertEqual(
                output['Destination well'].tolist(),
                ['A02', 'B01', 'C03', 'D04'],
            )
            self.assertFalse(
                output['Destination plate name'].astype(str).str.startswith('P016-').any()
            )


if __name__ == '__main__':
    unittest.main()
