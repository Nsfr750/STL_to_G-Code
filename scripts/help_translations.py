"""
Help system translations for STL to G-Code v{version}.
"""

# Help system translations organized by language
HELP_TRANSLATIONS = {
    "en": {
        # Help window
        "help.window_title": "Help - STL to G-Code",
        "help.buttons.documentation": "Online Documentation",
        "common.buttons.close": "Close",
        
        # Welcome tab
        "help.welcome.tab_title": "Welcome",
        "help.welcome.content": """
        <h2>Welcome to STL to G-Code</h2>
        <p>Thank you for choosing STL to G-Code, a powerful tool for converting your 3D models into 3D printing-ready G-code instructions.</p>
        
        <div class="note">
            <p><strong>Note:</strong> This application is under active development. If you encounter any issues or have suggestions, please don't hesitate to report them.</p>
        </div>
        
        <h3>Key Features:</h3>
        <ul>
            <li>STL file import</li>
            <li>Interactive 3D preview</li>
            <li>Customizable G-code generation</li>
            <li>Print path visualization</li>
            <li>Multi-language support</li>
        </ul>
        """,
        
        # Getting Started tab
        "help.getting_started.tab_title": "Getting Started",
        "help.getting_started.content": """
        <h2>Getting Started</h2>
        <ol>
            <li><strong>Open an STL file</strong> using File > Open or drag and drop</li>
            <li><strong>Adjust settings</strong> in the right panel to configure layer height, print speed, etc.</li>
            <li><strong>Preview the result</strong> to verify the output.</li>
            <li><strong>Generate G-code</strong> and save it to your computer.</li>
            <li><strong>Send to 3D printer</strong> or save to SD card.</li>
        </ol>
        
        <div class="tip">
            <p><strong>Tip:</strong> Start with conservative settings and adjust as needed.</p>
        </div>
        """,
        
        # Features tab
        "help.features.tab_title": "Features",
        "help.features.content": """
        <h2>Key Features</h2>
        
        <h3>File Management</h3>
        <p>Support for STL files with fast loading and 3D preview.</p>
        
        <h3>Customization</h3>
        <p>Numerous options to customize G-code generation to your needs.</p>
        
        <h3>3D Preview</h3>
        <p>Interactive visualization of the model and generated print paths.</p>
        
        <h3>Optimization</h3>
        <p>Advanced algorithms to optimize print paths and reduce print time.</p>
        """,
        
        # Shortcuts tab
        "help.shortcuts.tab_title": "Shortcuts",
        "help.shortcuts.content": """
        <h2>Keyboard Shortcuts</h2>
        
        <h3>General</h3>
        <ul>
            <li><strong>Ctrl+O</strong>: Open STL file</li>
            <li><strong>Ctrl+S</strong>: Save G-code</li>
            <li><strong>F1</strong>: Show help</li>
            <li><strong>F5</strong>: Refresh preview</li>
        </ul>
        
        <h3>3D Navigation</h3>
        <ul>
            <li><strong>Left-click + drag</strong>: Rotate view</li>
            <li><strong>Right-click + drag</strong>: Pan view</li>
            <li><strong>Mouse wheel</strong>: Zoom in/out</li>
        </ul>
        """,
        
        # Support tab
        "help.support.tab_title": "Support",
        "help.support.content": """
        <h2>Support</h2>
        
        <p>If you have questions or run into issues, here's how you can get help:</p>
        
        <h3>Documentation</h3>
        <p>Check out the online documentation for detailed guides and FAQs.</p>
        
        <h3>Issue Reporting</h3>
        <p>If you find a bug or have a feature request, please open an issue on GitHub.</p>

        """
    },
    "it": {
        # Help window
        "help.window_title": "Guida - STL a G-Code",
        "help.buttons.documentation": "Documentazione Online",
        "common.buttons.close": "Chiudi",
        
        # Welcome tab
        "help.welcome.tab_title": "Benvenuto",
        "help.welcome.content": """
        <h2>Benvenuto in STL a G-Code</h2>
        <p>Grazie per aver scelto STL a G-Code, un potente strumento per convertire i tuoi modelli 3D in istruzioni G-code pronte per la stampa 3D.</p>
        
        <div class="note">
            <p><strong>Nota:</strong> Questa applicazione è in fase di sviluppo attivo. Se riscontri problemi o hai suggerimenti, non esitare a segnalarli.</p>
        </div>
        
        <h3>Caratteristiche principali:</h3>
        <ul>
            <li>Importazione di file STL</li>
            <li>Anteprima 3D interattiva</li>
            <li>Generazione di G-code personalizzabile</li>
            <li>Anteprima dei percorsi di stampa</li>
            <li>Supporto multi-lingua</li>
        </ul>
        """,
        
        # Getting Started tab
        "help.getting_started.tab_title": "Per Iniziare",
        "help.getting_started.content": """
        <h2>Per Iniziare</h2>
        <ol>
            <li><strong>Apri un file STL</strong> utilizzando File > Apri STL o trascinando un file nella finestra.</li>
            <li><strong>Regola le impostazioni</strong> nel pannello di destra per configurare l'altezza degli strati, la velocità di stampa, ecc.</li>
            <li><strong>Visualizza l'anteprima</strong> per verificare il risultato finale.</li>
            <li><strong>Genera il G-code</strong> e salvalo sul tuo computer.</li>
            <li><strong>Invia alla stampante 3D</strong> o salva su scheda SD.</li>
        </ol>
        
        <div class="tip">
            <p><strong>Suggerimento:</strong> Inizia con impostazioni conservative e regola in base alle esigenze.</p>
        </div>
        """,
        
        # Features tab
        "help.features.tab_title": "Caratteristiche",
        "help.features.content": """
        <h2>Caratteristiche Principali</h2>
        
        <h3>Gestione File</h3>
        <p>Supporto per file STL con caricamento rapido e anteprima 3D.</p>
        
        <h3>Personalizzazione</h3>
        <p>Numerose opzioni per personalizzare la generazione del G-code in base alle tue esigenze.</p>
        
        <h3>Anteprima 3D</h3>
        <p>Visualizzazione interattiva del modello e dei percorsi di stampa generati.</p>
        
        <h3>Ottimizzazione</h3>
        <p>Algoritmi avanzati per ottimizzare i percorsi di stampa e ridurre i tempi di stampa.</p>
        """,
        
        # Shortcuts tab
        "help.shortcuts.tab_title": "Scorciatoie",
        "help.shortcuts.content": """
        <h2>Scorciatoie da Tastiera</h2>
        
        <h3>Generali</h3>
        <ul>
            <li><strong>Ctrl+O</strong>: Apri file STL</li>
            <li><strong>Ctrl+S</strong>: Salva G-code</li>
            <li><strong>F1</strong>: Mostra aiuto</li>
            <li><strong>F5</strong>: Aggiorna anteprima</li>
        </ul>
        
        <h3>Navigazione 3D</h3>
        <ul>
            <li><strong>Click sinistro + trascina</strong>: Ruota la vista</li>
            <li><strong>Click destro + trascina</strong>: Sposta la vista</li>
            <li><strong>Rotella del mouse</strong>: Zoom avanti/indietro</li>
        </ul>
        """,
        
        # Support tab
        "help.support.tab_title": "Supporto",
        "help.support.content": """
        <h2>Supporto</h2>
        
        <p>Se hai domande o hai riscontrato problemi, ecco come puoi ottenere aiuto:</p>
        
        <h3>Documentazione</h3>
        <p>Consulta la documentazione online per guide dettagliate e risposte alle domande più frequenti.</p>
        
        <h3>Segnalazione Problemi</h3>
        <p>Se riscontri un bug o hai una richiesta di funzionalità, apri una segnalazione su GitHub.</p>
        """
    }
}
