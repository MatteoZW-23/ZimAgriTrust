"""
USSD Language Support
Provides multi-language support for USSD menus (English, Shona, Ndebele)
"""

class USSDLanguage:
    """Multi-language support for USSD interface"""
    
    LANGUAGES = {
        "en": "English",
        "sn": "Shona",
        "nd": "Ndebele"
    }
    
    TRANSLATIONS = {
        # Root Menu
        "root_menu": {
            "en": (
                "CON 🇿🇼 ZimAgritrust Marketplace\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "1. Sell Product\n"
                "2. Buy Products\n"
                "3. AI Price Intel\n"
                "4. My Profile\n"
                "5. My Wallet\n"
                "6. Raise Dispute\n"
                "7. Change PIN\n"
                "8. Transactions\n"
                "9. Help\n"
                "0. Change Language"
            ),
            "sn": (
                "CON 🇿🇼 Musika weZimAgritrust\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "1. Tengesa Zvinhu\n"
                "2. Tenga Zvinhu\n"
                "3. Mitengo yeAI\n"
                "4. Profile Yangu\n"
                "5. Wallet Yangu\n"
                "6. Nyaya/Gakava\n"
                "7. Chinja PIN\n"
                "8. Zvakaitwa\n"
                "9. Rubatsiro\n"
                "0. Chinja Mutauro"
            ),
            "nd": (
                "CON 🇿🇼 Imakethe ye-ZimAgritrust\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "1. Thengisa Impahla\n"
                "2. Thenga Impahla\n"
                "3. Intengo ye-AI\n"
                "4. Iphrofayili Yami\n"
                "5. I-Wallet Yami\n"
                "6. Phakamisa Ingxabano\n"
                "7. Guqula i-PIN\n"
                "8. Okwenziwayo\n"
                "9. Usizo\n"
                "0. Guqula Ulimi"
            )
        },
        
        # Common phrases
        "enter_pin": {
            "en": "CON Enter your secret 4-digit PIN",
            "sn": "CON Isa PIN yako ye4-digit",
            "nd": "CON Faka i-PIN yakho ye-4-digit"
        },
        
        "incorrect_pin": {
            "en": "CON Incorrect PIN. Try again:",
            "sn": "CON PIN isiri iyo. Edza zvakare:",
            "nd": "CON I-PIN ayilungile. Zama futhi:"
        },
        
        "invalid_option": {
            "en": "END Invalid option. Dial *123# again.",
            "sn": "END Sarudzo isiri iyo. Fona *123# zvakare.",
            "nd": "END Inketho engalungile. Shayela *123# futhi."
        },
        
        # Sell flow
        "sell_step1": {
            "en": "CON [SELL] Step 1/5\nEnter product name (e.g. Maize)",
            "sn": "CON [TENGESA] Danho 1/5\nIsa zita rechigadzirwa (somuenzaniso Chibage)",
            "nd": "CON [THENGISA] Isinyathelo 1/5\nFaka igama lomkhiqizo (isib. Umbila)"
        },
        
        "sell_quantity": {
            "en": "CON Enter quantity in kilograms",
            "sn": "CON Isa huwandu mumakirogiramu",
            "nd": "CON Faka inani ngamakhilogremu"
        },
        
        "sell_grade": {
            "en": "CON Enter product grade (A/B/C)",
            "sn": "CON Isa giredhi rechigadzirwa (A/B/C)",
            "nd": "CON Faka igreyidi yomkhiqizo (A/B/C)"
        },
        
        "sell_price": {
            "en": "CON Enter price per kg (USD)",
            "sn": "CON Isa mutengo pa kg (USD)",
            "nd": "CON Faka intengo nge-kg (USD)"
        },
        
        "sell_location": {
            "en": "CON Enter province (e.g. Harare, Bulawayo)",
            "sn": "CON Isa dunhu (somuenzaniso Harare, Bulawayo)",
            "nd": "CON Faka isifundazwe (isib. Harare, Bulawayo)"
        },
        
        "listing_created": {
            "en": "END ✅ Listing Created!",
            "sn": "END ✅ Runyorwa Rwakagadzirwa!",
            "nd": "END ✅ Uhlu Lwenziwe!"
        },
        
        # Buy flow
        "available_products": {
            "en": "CON Available Products:",
            "sn": "CON Zvinhu Zviripo:",
            "nd": "CON Imikhiqizo Etholakalayo:"
        },
        
        "no_products": {
            "en": "END No products available at the moment.",
            "sn": "END Hapana zvinhu zviripo parizvino.",
            "nd": "END Akukho mikhiqizo etholakalayo okwamanje."
        },
        
        "enter_quantity_buy": {
            "en": "CON Enter quantity to buy (kg)",
            "sn": "CON Isa huwandu hwekutenga (kg)",
            "nd": "CON Faka inani lokuthenga (kg)"
        },
        
        "confirm_purchase": {
            "en": "CON Confirm Purchase:",
            "sn": "CON Simbisa Kutenga:",
            "nd": "CON Qinisekisa Ukuthenga:"
        },
        
        "offer_sent": {
            "en": "END ✅ Offer Sent!",
            "sn": "END ✅ Chipo Chatumirwa!",
            "nd": "END ✅ Isipho Sithunyelwe!"
        },
        
        # Profile
        "profile": {
            "en": "END 👤 PROFILE",
            "sn": "END 👤 PROFILE",
            "nd": "END 👤 IPHROFAYILI"
        },
        
        "trust_score": {
            "en": "Trust Score:",
            "sn": "Chiyero cheKuvimba:",
            "nd": "Isikolo Sokuthembeka:"
        },
        
        # Wallet
        "wallet": {
            "en": "END 💰 WALLET (USD)",
            "sn": "END 💰 WALLET (USD)",
            "nd": "END 💰 I-WALLET (USD)"
        },
        
        "released": {
            "en": "Released:",
            "sn": "Yakaburitswa:",
            "nd": "Ikhishiwe:"
        },
        
        "in_escrow": {
            "en": "In Escrow:",
            "sn": "Mune Escrow:",
            "nd": "Ku-Escrow:"
        },
        
        # Help
        "help": {
            "en": "END 📖 HELP",
            "sn": "END 📖 RUBATSIRO",
            "nd": "END 📖 USIZO"
        },
        
        # Language selection
        "select_language": {
            "en": "CON Select Language:\n1. English\n2. Shona\n3. Ndebele",
            "sn": "CON Sarudza Mutauro:\n1. English\n2. Shona\n3. Ndebele",
            "nd": "CON Khetha Ulimi:\n1. English\n2. Shona\n3. Ndebele"
        },
        
        "language_changed": {
            "en": "END Language changed to English",
            "sn": "END Mutauro wachinjwa kuenda kuShona",
            "nd": "END Ulimi luguqulelwe ku-Ndebele"
        }
    }
    
    @classmethod
    def get_text(cls, key: str, lang: str = "en", **kwargs) -> str:
        """
        Get translated text for a given key
        
        Args:
            key: Translation key
            lang: Language code (en, sn, nd)
            **kwargs: Format parameters
        
        Returns:
            Translated text
        """
        if lang not in cls.LANGUAGES:
            lang = "en"
        
        text = cls.TRANSLATIONS.get(key, {}).get(lang, cls.TRANSLATIONS.get(key, {}).get("en", ""))
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        
        return text
    
    @classmethod
    def get_language_code(cls, selection: str) -> str:
        """Convert menu selection to language code"""
        mapping = {
            "1": "en",
            "2": "sn",
            "3": "nd"
        }
        return mapping.get(selection, "en")
