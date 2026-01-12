# from text_extractor import TextExtractor

# extractor = TextExtractor()
# result = extractor.extract(r"/home/abhishekchoudhary/Desktop/notary_project/Notaria/Acrisound/ACRISOUND. Certificacion legalizada y apostillada.pdf")

# print("=== FULL TEXT ===")
# print(result.full_text[:3000])

# print("\n=== PAGE TRACE ===")
# for p in result.pages:
#     print(f"Page {p.page_number} | Source: {p.source} | Chars: {len(p.text)}")
# from text_extractor import TextExtractor
# from field_extractor import FieldExtractor

# extractor = TextExtractor()
# text_result = extractor.extract(r"/home/abhishekchoudhary/Desktop/notary_project/Notaria/Acrisound/ACRISOUND. Certificacion legalizada y apostillada.pdf")

# field_extractor = FieldExtractor()
# fields = field_extractor.extract_personeria_juridica(text_result.full_text)

# print(fields)


from pipeline import CertificatePipeline

pipeline = CertificatePipeline(
    legal_rules_path="./legal/legal_rules.json"
)

result = pipeline.run(
    certificate_type="certificado_firmas",
    document_paths=[
        "./Notaria/Acrisound/ACRISOUND. Certificacion legalizada y apostillada.pdf"
    ]
)

print(result)
