// $Id: $

"use strict";

let sms = {};

Components.utils.import("resource://gre/modules/Services.jsm");

var SMSearchEngineAdd = {
  onLoad: function SMS_onLoad() {
    window.removeEventListener("load", SMS_onLoad, false);
    window.addEventListener("unload", SMSearchEngineAdd.onUnload, false);
    gBrowser.addEventListener("DOMLinkAdded", SMSearchEngineAdd.onLinkAdded, false);
    // for FormHistoryControl integration
    let searchbar = document.getElementById("searchbar");
    if (searchbar) {
      let searchbarBox = document.getAnonymousElementByAttribute(searchbar, "anonid", "searchbar-textbox");
      searchbarBox.addEventListener("popupshown", SMSearchEngineAdd.onPopupshown, false);
    }
  },
  
  onUnload: function SMS_onUnload() {
    window.removeEventListener("unload", SMS_onUnload, false);
    gBrowser.removeEventListener("DOMLinkAdded", SMSearchEngineAdd.onLinkAdded, true);
  },
  
  onPopupshown: function SMS_onPopupshown(evt) {
    if (FhcShowDialog) {
      // FormHistoryControl is installed
      try {
        let fhc = {};
        Services.scriptloader.loadSubScript("chrome://formhistory/content/overlay/FhcSearchbarOverlay.js", fhc);
        fhc.FhcSearchbarOverlay.popupshown(evt);
      } catch (exc) {
        Components.utils.reportError(exc);
      }
    }
  },
  
  get searchBar() {
    return document.getElementById("searchbar");
  },

  //***************************************************************************
  //* this code is courtesy of mozilla-central/browser/base/content/browser.js
  //*   addEngine has not been modified at all,
  //*   onLinkAdded has been shortened and modified to add all found engines.
  //***************************************************************************

  addEngine: function(engine, targetDoc) {
    if (!this.searchBar)
      return;

    var browser = gBrowser.getBrowserForDocument(targetDoc);
    // ignore search engines from subframes (see bug 479408)
    if (!browser)
      return;

    // Check to see whether we've already added an engine with this title
    if (browser.engines) {
      if (browser.engines.some(function (e) e.title == engine.title))
        return;
    }

    // Append the URI and an appropriate title to the browser data.
    // Use documentURIObject in the check for shouldLoadFavIcon so that we
    // do the right thing with about:-style error pages.  Bug 453442
    var iconURL = null;
    if (gBrowser.shouldLoadFavIcon(targetDoc.documentURIObject))
      iconURL = targetDoc.documentURIObject.prePath + "/favicon.ico";

    var hidden = false;
    // If this engine (identified by title) is already in the list, add it
    // to the list of hidden engines rather than to the main list.
    // XXX This will need to be changed when engines are identified by URL;
    // see bug 335102.
    if (Services.search.getEngineByName(engine.title))
      hidden = true;

    var engines = (hidden ? browser.hiddenEngines : browser.engines) || [];

    engines.push({ uri: engine.href,
                   title: engine.title,
                   icon: iconURL });

    if (hidden)
      browser.hiddenEngines = engines;
    else
      browser.engines = engines;
  },
  
  onLinkAdded: function SMS_onLinkAdded(event) {
    var link = event.originalTarget;
    var rel = link.rel && link.rel.toLowerCase();
    if (!link || !link.ownerDocument || !rel || !link.href)
      return;

    var relStrings = rel.split(/\s+/);
    var rels = {};
    for (let i = 0; i < relStrings.length; i++)
      rels[relStrings[i]] = true;

    for (let relVal in rels) {
      if (relVal == "search") {
        var type = link.type && link.type.toLowerCase();
        type = type.replace(/^\s+|\s*(?:;.*)?$/g, "");
        let privateBrowsing = false; // SM doesn't have private browsing yet...
        try { privateBrowsing = gPrivateBrowsingUI.privateBrowsingEnabled; } catch (e) {}

        if (type == "application/opensearchdescription+xml" && link.title &&
            /^(?:https?|ftp):/i.test(link.href) &&
            !privateBrowsing) {
          var engine = { title: link.title, href: link.href };
          SMSearchEngineAdd.addEngine(engine, link.ownerDocument);
        }
      }
    }
  }

  // End mozilla-central code

}

window.addEventListener("load", SMSearchEngineAdd.onLoad, false);
