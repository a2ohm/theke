var currentWord;
var currentVerse;

function upTo(el, id) {
    // Find first ancestor of el with class

    while (el && el.parentNode) {
        el = el.parentNode;
        if (el.className && el.className == id) {
            return el;
        }
    }

    return null;
  }

function jump_to_verse(verseTag) {
    var verse_to_scroll_to = document.getElementById(verseTag);

    if (verse_to_scroll_to != null) {
        // Unselect previous verse
        if (currentVerse != null) {
            currentVerse.classList.remove("em");
        }

        // Select this verse
        currentVerse = verse_to_scroll_to;
        currentVerse.classList.add("em");

        currentVerse.scrollIntoView({behavior: "smooth", block: "center", inline: "nearest"});
    }
}

function handle_click_on_word(evt) {
    word = evt.target.innerText;
    morph = evt.target.getAttribute("morph");
    lemma = evt.target.getAttribute("lemma");

    if ((morph != null) || (lemma != null)) {
        if (morph == null) { morph = ''; } else { morph = morph.replace(/\//g, '_'); }
        if (lemma == null) { lemma = ''; }

        // Unselect previous word
        if (currentWord != null) {
            currentWord.classList.remove("selected");
        }
        
        // Select this word
        currentWord = evt.target;
        currentWord.classList.add("selected");

        // Get the source of this word
        parentCol = upTo(currentWord, "content-col")
        source = parentCol.getAttribute("source")

        // Send its morphology out of the webview
        r = "theke:/signal/click_on_word?word=" + word + "&morph=" + morph + "&lemma=" + lemma + "&source=" + source;
        fetch(r);
    }
}

document.getElementById("content").addEventListener('click', handle_click_on_word);