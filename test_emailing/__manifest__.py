# Copyright 2020 O4SB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Test Emailing",
    "summary": """
        Emailing within system for test purpose""",
    "version": "18.1.0.0",
    "license": "AGPL-3",
    "author": "Open For Small Business Ltd, OdooNZ",
    "category": "Testing",
    "depends": ["mail"],
    "data": [
        "security/test_emailing.xml",
        "security/ir.model.access.csv",
        "views/test_emailing.xml"
    ],
}
