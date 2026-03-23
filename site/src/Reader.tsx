import { useState, useCallback } from "react";
import { ReactReader } from "react-reader";

function Reader() {
  const [location, setLocation] = useState<string | number>(0);

  const locationChanged = useCallback((loc: string) => {
    setLocation(loc);
  }, []);

  return (
    <div className="min-h-screen bg-ink flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 bg-ink px-6 py-3 flex items-center justify-between">
        <a href="/" className="text-sm font-semibold text-white/80 hover:text-white transition-colors">
          postwriter
        </a>
        <div className="text-center">
          <span className="text-sm text-white/60">Black Meat</span>
          <span className="mx-2 text-white/20">|</span>
          <span className="text-xs text-accent">Generated in a single session</span>
        </div>
        <a
          href="/"
          className="text-xs text-white/40 hover:text-white/70 transition-colors"
        >
          Back to postwriter.app
        </a>
      </header>

      {/* Reader — react-reader needs a fixed-height container */}
      <div style={{ height: "calc(100vh - 52px)", position: "relative" }}>
        <ReactReader
          url="/black-meat-fast-draft.epub"
          location={location}
          locationChanged={locationChanged}
          epubOptions={{
            flow: "paginated",
            manager: "default",
          }}
          getRendition={(rendition) => {
            rendition.themes.default({
              body: {
                "font-family": "Georgia, 'Times New Roman', serif !important",
                "line-height": "1.7 !important",
                color: "#1a1a1a !important",
                "padding": "0 1em !important",
              },
              p: {
                "text-align": "justify !important",
                "text-indent": "1.5em !important",
                "margin": "0.6em 0 !important",
              },
              "p:first-of-type": {
                "text-indent": "0 !important",
              },
            });
          }}
        />
      </div>
    </div>
  );
}

export default Reader;
