"""Регрессионные проверки: не путать критически разные варианты товаров."""
import unittest
from matching_engine import Matcher, build_product, normalize
from spreadsheet_io import read_first_sheet, update_xlsx
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from pathlib import Path

def make_catalog(names):
    return [build_product(i+2,name,f"https://example.org/{i}.webp")
            for i,name in enumerate(names)]

class MatchingTests(unittest.TestCase):
    def test_identical_item(self):
        p=build_product(4,"Ferplast Ножницы для шерсти GRO 5989")
        found=Matcher(make_catalog(["Ferplast Ножницы для шерсти GRO 5989"])).match(p)
        self.assertEqual(found.status,"Надёжно")
        self.assertEqual(found.product.name,p.name)

    def test_model_variant_is_not_swapped(self):
        p=build_product(4,"Ferplast Ножницы для шерсти GRO 5989")
        result=Matcher(make_catalog(["Ferplast Ножницы для шерсти GRO 5988"])).match(p)
        self.assertIsNone(result.product)

    def test_weight_variant_is_not_swapped(self):
        q=build_product(8,"Monge корм для кошек с индейкой 5кг")
        result=Matcher(make_catalog(["Monge корм для кошек с индейкой 500г"])).match(q)
        self.assertIsNone(result.product)

    def test_species_variant_is_not_swapped(self):
        q=build_product(10,"Amity корм для кошек с курицей")
        r=Matcher(make_catalog(["Amity корм для собак с курицей"])).match(q)
        self.assertIsNone(r.product)

    def test_different_protein_is_not_swapped(self):
        q=build_product(8,"Royal Canin корм для кошек с говядиной")
        r=Matcher(make_catalog(["Royal Canin корм для кошек с курицей"])).match(q)
        self.assertIsNone(r.product)

    def test_color_not_swapped(self):
        q=build_product(8,"Толстовка Texas 25 см желтый")
        r=Matcher(make_catalog(["Толстовка Texas 25 cm черный"])).match(q)
        self.assertIsNone(r.product)

    def test_brand_alias(self):
        q=build_product(8,"Роял Канин для взрослых кошек")
        r=Matcher(make_catalog(["Royal Canin для взрослых кошек"])).match(q)
        self.assertIsNotNone(r.product)

    def test_brand_lines_are_not_swapped(self):
        q=build_product(10,"Санабелль Лайт корм для кошек 2кг")
        r=Matcher(make_catalog(["Bosch Sanabelle Dental Cat"])).match(q)
        self.assertIsNone(r.product)

    def test_named_line_is_not_replaced_with_another(self):
        q=build_product(10,"Акана Баунтифул Кэтч для кошек")
        r=Matcher(make_catalog(["ACANA Pacifica Cat"])).match(q)
        self.assertIsNone(r.product)

    def test_shorthand_size_variant(self):
        q=build_product(10,"Brit Care Dog Puppy&Junior M Healthy Growth")
        r=Matcher(make_catalog(["Brit Care Dog Puppy&Junior S Healthy Growth"])).match(q)
        self.assertIsNone(r.product)

    def test_medication_dose_is_not_swapped(self):
        q=build_product(10,"Препарат Cat 60мг")
        r=Matcher(make_catalog(["Препарат Cat 30мг"])).match(q)
        self.assertIsNone(r.product)

    def test_normalization_is_deterministic(self):
        self.assertEqual(normalize("ГРО 5938; Д/кош."),normalize("ГРО 5938; Д/кош."))

    def test_write_preserves_original_cells(self):
        with TemporaryDirectory() as temp:
            original=Path(temp)/"Вход.xlsx"
            out=Path(temp)/"Результат.xlsx"
            xml='''<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<dimension ref="A1:L4"/><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Место</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Номенклатура</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Склад</t></is></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Товар</t></is></c><c r="B4"><v>9</v></c></row>
</sheetData></worksheet>'''.encode('utf-8')
            with ZipFile(original,"w") as z:
                z.writestr("xl/worksheets/sheet1.xml",xml)
                z.writestr("extra.txt","прежний")
            update_xlsx(original,out,{4:{"url":"https://example.org/p.webp","status":"Надёжно","confidence":.98}})
            contents={r.row:r.data for r in read_first_sheet(out)}
            self.assertEqual(contents[4]["A"],"Товар")
            self.assertEqual(contents[4]["B"],"9")
            self.assertEqual(contents[4]["M"],"https://example.org/p.webp")
            self.assertEqual(contents[4]["O"],"0.98")
            with ZipFile(out) as z: self.assertEqual(z.read("extra.txt"),b"\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb6\xd0\xbd\xd0\xb8\xd0\xb9")

if __name__ == "__main__":
    unittest.main()
