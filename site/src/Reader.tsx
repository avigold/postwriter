import { useState, useCallback } from "react";
import { ReactReader, ReactReaderStyle, type IReactReaderStyle } from "react-reader";

// Dark theme: override only colours from the default ReactReaderStyle
const darkStyles: IReactReaderStyle = {
  ...ReactReaderStyle,
  readerArea: {
    ...ReactReaderStyle.readerArea,
    backgroundColor: "#1a1a1a",
  },
  titleArea: {
    ...ReactReaderStyle.titleArea,
    color: "#666",
  },
  arrow: {
    ...ReactReaderStyle.arrow,
    color: "#555",
  },
  arrowHover: {
    ...ReactReaderStyle.arrowHover,
    color: "#999",
  },
  tocArea: {
    ...ReactReaderStyle.tocArea,
    background: "#111",
  },
  tocAreaButton: {
    ...ReactReaderStyle.tocAreaButton,
    color: "#aaa",
    borderBottom: "1px solid #333",
  },
  tocButtonExpanded: {
    ...ReactReaderStyle.tocButtonExpanded,
    background: "#222",
  },
  tocButtonBar: {
    ...ReactReaderStyle.tocButtonBar,
    background: "#ccc",
  },
  tocButtonBarTop: {
    ...ReactReaderStyle.tocButtonBarTop,
  },
  tocButtonBottom: {
    ...ReactReaderStyle.tocButtonBottom,
  },
  loadingView: {
    ...ReactReaderStyle.loadingView,
    color: "#666",
  },
};

function Reader() {
  // Start on the title page, skipping the auto-generated TOC nav page
  const [location, setLocation] = useState<string | number>("title.xhtml");

  const locationChanged = useCallback((loc: string) => {
    setLocation(loc);
  }, []);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: "#1a1a1a" }}>
      {/* Header */}
      <header style={{
        borderBottom: "1px solid #333",
        background: "#111",
        padding: "10px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexShrink: 0,
      }}>
        <a href="/" style={{ color: "#ccc", textDecoration: "none", fontSize: 14, fontWeight: 600 }}>
          postwriter
        </a>
        <div style={{ textAlign: "center" }}>
          <span style={{ color: "#999", fontSize: 14 }}>Black Meat</span>
          <span style={{ color: "#444", margin: "0 8px" }}>|</span>
          <span style={{ color: "#777", fontSize: 12 }}>by Postwriter</span>
          <span style={{ color: "#444", margin: "0 8px" }}>|</span>
          <span style={{ color: "#8b5cf6", fontSize: 12 }}>generated in a single session</span>
        </div>
        <a href="/" style={{ color: "#999", textDecoration: "none", fontSize: 13 }}>
          &larr; Back
        </a>
      </header>

      {/* Reader */}
      <div style={{ flexGrow: 1, position: "relative" }}>
        <ReactReader
          url="/black-meat-fast-draft.epub"
          location={location}
          locationChanged={locationChanged}
          readerStyles={darkStyles}
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
              },
              h1: {
                color: "#ddd !important",
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
            });
          }}
        />
      </div>
    </div>
  );
}

export default Reader;
