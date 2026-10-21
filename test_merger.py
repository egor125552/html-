"""Регрессионные проверки: не путать критически разные варианты товаров."""
import unittest
from matching_engine import Matcher, Match, build_product, normalize
from rescue_matching import rescue
from anchor_matching import anchor_match
from sitemap_matching import canonical_title, latin, SitemapMatcher, image_url
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

    def test_rescue_rejects_generic_similar_products(self):
        q=build_product(15,"Игрушка для собак синий мяч")
        r=Matcher(make_catalog(["Игрушка для собак синяя косточка"]))
        preliminary=Match(None,.48,"Нет совпадения","неизвестно",((.48,r.catalog[0]),))
        found=rescue(r,q,preliminary)
        self.assertIsNone(found.product)

    def test_rescue_never_overrides_conflicting_size(self):
        q=build_product(15,"Лакомство Cibau с индейкой 800г")
        r=Matcher(make_catalog(["Cibau лакомство с индейкой 80г"]))
        found=rescue(r,q,r.match(q))
        self.assertIsNone(found.product)

    def test_abbreviations_represent_same_flavour(self):
        a=build_product(15,"AlphaPet сЧП Утк.клюк.мяс.кус.соус")
        b=build_product(3,"AlphaPet Superpremium Утка и клюква мясные кусочки в соусе")
        self.assertIn("duck",a.flavors)
        self.assertIn("duck",b.flavors)
        self.assertTrue(a.tokens & b.tokens)

    def test_sitemap_transliteration(self):
        self.assertEqual(canonical_title("govyadina-s-kuritsey"),"beef chicken")
        self.assertEqual(latin("Санабелль"),"sanabell")

    def test_sitemap_rejects_wrong_species(self):
        xml = '''<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
<url><loc>https://garfield.by/catalog/cats/farmina-gastro.html</loc>
<image:image><image:loc>https://garfield.by/image.jpg</image:loc></image:image></url>
</urlset>'''
        with TemporaryDirectory() as folder:
            file=Path(folder)/"site.xml"
            file.write_text(xml,encoding="utf-8")
            found=SitemapMatcher(file).match(build_product(10,"Farmina Gastro для собак"))
            self.assertIsNone(found)

    def test_medicine_name_cannot_be_substituted(self):
        q=build_product(10,"Ципровет для кошек")
        r=Matcher(make_catalog(["Бимаксгард для кошек"]))
        self.assertIsNone(r.match(q).product)

    def test_snack_shape_cannot_be_substituted(self):
        q=build_product(10,"Мясная нарезка для собак")
        r=Matcher(make_catalog(["Мясная косичка для собак"]))
        self.assertIsNone(r.match(q).product)

    def test_fractional_medication_strength_is_preserved(self):
        from matching_engine import units
        self.assertIn(("dose", 5.4), units("Апоквел 5,4 мг"))
        self.assertIn(("dose", 5.5), units("Апоквел 5,5 мг"))
        self.assertNotEqual(units("Апоквел 5,4 мг"),units("Апоквел 5,5 мг"))

    def test_fractional_pipette_volume_is_preserved(self):
        from matching_engine import units
        self.assertIn(("volume", 0.5), units("Капли 0,5 мл"))
        self.assertIn(("volume", 0.8), units("Капли 0,8 мл"))
        self.assertNotEqual(units("Капли 0,5 мл"),units("Капли 0,8 мл"))

    def test_terminal_dot_does_not_create_new_token(self):
        self.assertEqual(normalize("свинок."),normalize("свинок"))

    def test_anchor_finds_distinctive_product_series(self):
        q=build_product(10,"CAVIA COMPLETE полноценный корм для морских свинок 1,75 кг")
        c=make_catalog(["Versele Laga Корм Cavia Complete",
                        "Bambini Pets корм для морских свинок",
                        "Bambini Pets корм для крыс"])
        found=anchor_match(Matcher(c),q)
        self.assertIsNotNone(found)
        self.assertIn("Cavia Complete",found.product.name)

    def test_anchor_does_not_swap_flavours(self):
        q=build_product(10,"Cat Step Arctic Lavender наполнитель д/кошек 3,8 л")
        c=make_catalog(["Cat Step Arctic Breeze","Cat Step Arctic Fresh Mint"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_anchor_does_not_swap_medication_doses(self):
        q=build_product(10,"Апоквел 5,4 мг 100 табл")
        c=make_catalog(["Апоквел 5,5 мг","Апоквел 3,6 мг"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_anchor_unique_drug_dose(self):
        q=build_product(10,"Апоквел 5,4 мг 100 табл")
        c=make_catalog(["Zoetis Апоквел 5,4 мг","Zoetis Апоквел 3,6 мг"])
        found=anchor_match(Matcher(c),q)
        self.assertIsNotNone(found)
        self.assertIn("5,4",found.product.name)

    def test_anchor_rejects_different_toy_animal(self):
        q=build_product(10,"Toy Dog Aqua Alaska Walrus TPR")
        c=make_catalog(["Hunter Игрушка для собак Aqua Alaska Octopus"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_anchor_rejects_food_replaced_with_snack(self):
        q=build_product(10,"Mini France 24/12 Утка картофель 0,8 кг")
        c=make_catalog(["Happy Dog Soft Snack France (Утка картофель)"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_anchor_rejects_brandless_generic_ingredient(self):
        q=build_product(10,"Сердце говяжье 1 кг")
        c=make_catalog(["Clan Pride Консервы Говяжье сердце и печень"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_anchor_rejects_source_brand_not_on_product(self):
        q=build_product(10,"Уши кроличьи с мясом утки Деревенские лакомства 90г")
        c=make_catalog(["AlpenHof Уши кроличьи с мясом утки"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_british_shorthair_breed_is_not_brit_brand(self):
        q=build_product(10,"BRITISH SHORTHAIR ADULT (Брит короткошерстная)")
        r=Matcher(make_catalog(["Royal Canin British Shorthair Adult для кошек"]))
        self.assertNotIn("другая марка",r._conflicts(q,r.catalog[0])[0])
        
    def test_image_url_encodes_spaces_and_unicode(self):
        url="https://garfield.by/upload/iblock/Сухой корм (1).webp"
        fixed=image_url(url)
        self.assertNotIn(" ",fixed)
        self.assertIn("%20",fixed)
        self.assertIn("%D0%A1",fixed)

    def test_buffalo_cannot_be_replaced_with_cod(self):
        q=build_product(10,"MONGE BWILD корм с мясом буйвола для кошек")
        r=Matcher(make_catalog(["Monge Cat Bwild (Треска) для кошек"]))
        self.assertIsNone(r.match(q).product)

    def test_green_abbreviation_cannot_be_replaced_with_pink(self):
        q=build_product(10,"Мяч зелён.5см")
        r=Matcher(make_catalog(["Мяч розовый 5 см"]))
        self.assertIsNone(r.match(q).product)

    def test_frosty_treat_cannot_be_replaced_with_canned_food(self):
        q=build_product(10,'Мнямс Лакомство Фросты из курицы для собак')
        r=Matcher(make_catalog(['Мнямс Консервы для щенков с курицей']))
        self.assertIsNone(r.match(q).product)

    def test_sticks_cannot_be_replaced_with_cream(self):
        q=build_product(10,'Мнямс Лакомство с цыпленком и печенью для кошек Палочки')
        r=Matcher(make_catalog(['Мнямс Крем-лакомство для кошек с курицей']))
        self.assertIsNone(r.match(q).product)

    def test_canin_short_form_means_royal_canin_brand(self):
        q=build_product(10,"GASTRO INTESTINAL LOW FAT CANIN 420г для собак")
        target=build_product(12,"Cennamo HT Diet Gastro intestinal")
        r=Matcher([target.__class__(**{**target.__dict__,"url":"https://example.org/x.jpg"})])
        self.assertTrue(r._conflicts(q,r.catalog[0])[0])

    def test_different_protein_not_masked_by_shared_liver(self):
        q=build_product(10,"WANPY Говяжья печень для собак")
        m=Matcher(make_catalog(["Wanpy Курица и печень для собак"]))
        self.assertIsNone(m.match(q).product)

    def test_named_toy_shapes_cannot_be_swapped(self):
        q=build_product(10,"Игрушка Mr.Kranch Огурчик для кошек")
        m=Matcher(make_catalog(["Mr.Kranch Лобстер для кошек"]))
        self.assertIsNone(m.match(q).product)

    def test_named_bowl_series_cannot_be_swapped(self):
        q=build_product(10,"Миска Mr.Kranch Candy")
        m=Matcher(make_catalog(["Mr.Kranch Миска Diamond"]))
        self.assertIsNone(m.match(q).product)

    def test_named_liver_brand_cannot_be_swapped(self):
        q=build_product(10,'Печень говяжья "Нюша" 50 г')
        m=Matcher(make_catalog(["ТИТБИТ Печень говяжья для кошек"]))
        self.assertIsNone(m.match(q).product)

    def test_brand_selection_prefers_first_label_over_generic_collar(self):
        p=build_product(10,"Trixie Ошейник Premium Collar Blue")
        self.assertEqual(p.brand,"trixie")
        q=build_product(10,"Ошейник, Collar Neoprene VP синий")
        self.assertEqual(q.brand,"collar")
        m=Matcher(make_catalog(["Trixie Ошейник Premium Collar Blue"]))
        self.assertIsNone(m.match(q).product)

    def test_anchor_does_not_assign_brand_to_generic_duck_feet(self):
        q=build_product(10,"Лапки утиные 50 шт")
        c=make_catalog(["Бобик-Снобик лапки утиные"])
        self.assertIsNone(anchor_match(Matcher(c),q))

    def test_medicine_product_line_is_not_mistaken_for_manufacturer(self):
        q=build_product(10,"Празицид-комплекс НЕО для кошек")
        m=Matcher(make_catalog(["Apicenna Празицид-комплекс НЕО для кошек"]))
        self.assertNotIn("другая марка",m._conflicts(q,m.catalog[0])[0])

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
