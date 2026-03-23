import { useState, useCallback } from "react";
import { ReactReader, type IReactReaderStyle } from "react-reader";

const darkReaderStyles: IReactReaderStyle = {
  container: {
    overflow: "hidden",
    height: "100%",
  },
  readerArea: {
    backgroundColor: "#1a1a1a",
    transition: undefined,
    position: "relative",
  },
  containerExpanded: {
    transform: "translateX(256px)",
  },
  titleArea: {
    color: "#999",
    textAlign: "center",
    padding: "10px 0",
  },
  reader: {
    position: "absolute",
    top: 50,
    left: 50,
    bottom: 20,
    right: 50,
  },
  swipeWrapper: {
    position: "absolute",
    top: 0,
    left: 0,
    bottom: 0,
    right: 0,
    zIndex: 200,
  },
  prev: {
    left: 1,
    top: "50%",
    marginTop: -32,
    color: "#666",
    fontSize: 64,
    padding: "0 10px",
    cursor: "pointer",
    position: "absolute",
    background: "none",
    border: "none",
  },
  next: {
    right: 1,
    top: "50%",
    marginTop: -32,
    color: "#666",
    fontSize: 64,
    padding: "0 10px",
    cursor: "pointer",
    position: "absolute",
    background: "none",
    border: "none",
  },
  tocBackground: {
    background: "rgba(0,0,0,0.6)",
    position: "absolute",
    left: 256,
    top: 0,
    bottom: 0,
    right: 0,
    zIndex: 1,
  },
  tocArea: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    zIndex: 0,
    width: 256,
    overflowY: "auto",
    WebkitOverflowScrolling: "touch",
    background: "#111",
    padding: "10px 0",
  },
  tocAreaButton: {
    userSelect: "none",
    appearance: "none",
    background: "none",
    border: "none",
    display: "block",
    fontFamily: "sans-serif",
    width: "100%",
    fontSize: 14,
    textAlign: "left",
    padding: "12px 20px",
    color: "#bbb",
    cursor: "pointer",
  },
  tocButtonExpanded: {
    background: "#222",
  },
  tocButton: {
    background: "none",
    border: "none",
    width: 32,
    height: 32,
    position: "absolute",
    top: 10,
    left: 10,
    borderRadius: 2,
    outline: "none",
    cursor: "pointer",
  },
  loadingView: {
    position: "absolute",
    top: "50%",
    left: "10%",
    right: "10%",
    color: "#666",
    textAlign: "center",
    marginTop: "-1em",
  },
};

function Reader() {
  const [location, setLocation] = useState<string | number>(0);

  const locationChanged = useCallback((loc: string) => {
    setLocation(loc);
  }, []);

  return (
    <div className="min-h-screen bg-[#1a1a1a] flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 bg-[#111] px-6 py-3 flex items-center justify-between">
        <a href="/" className="text-sm font-semibold text-white/80 hover:text-white transition-colors">
          postwriter
        </a>
        <div className="text-center">
          <span className="text-sm text-white/60">Black Meat</span>
          <span className="mx-2 text-white/20">|</span>
          <span className="text-xs text-white/40">by Avram Score</span>
          <span className="mx-2 text-white/20">|</span>
          <span className="text-xs text-accent">generated in a single session</span>
        </div>
        <a
          href="/"
          className="text-xs text-white/40 hover:text-white/70 transition-colors"
        >
          postwriter.app
        </a>
      </header>

      {/* Reader */}
      <div style={{ height: "calc(100vh - 52px)", position: "relative" }}>
        <ReactReader
          url="/black-meat-fast-draft.epub"
          location={location}
          locationChanged={locationChanged}
          readerStyles={darkReaderStyles}
          epubOptions={{
            flow: "paginated",
            manager: "default",
          }}
          getRendition={(rendition) => {
            rendition.themes.default({
              body: {
                "font-family": "Georgia, 'Times New Roman', serif !important",
                "line-height": "1.8 !important",
                color: "#ccc !important",
                background: "#1a1a1a !important",
                padding: "0 1em !important",
              },
              p: {
                "text-align": "justify !important",
                "text-indent": "1.5em !important",
                margin: "0.7em 0 !important",
              },
              "p:first-of-type": {
                "text-indent": "0 !important",
              },
              h1: {
                color: "#e5e5e5 !important",
                "text-align": "center !important",
              },
              em: {
                "font-style": "italic !important",
              },
              ".chapter-number": {
                color: "#666 !important",
              },
              ".scene-break": {
                color: "#555 !important",
              },
              ".title-page h1": {
                color: "#e5e5e5 !important",
              },
              ".title-page .author": {
                color: "#999 !important",
              },
            });
          }}
        />
      </div>
    </div>
  );
}

export default Reader;
