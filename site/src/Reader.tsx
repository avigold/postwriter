import { useState, useCallback } from "react";
import { ReactReader } from "react-reader";

function Reader() {
  const [location, setLocation] = useState<string | number>(0);

  const locationChanged = useCallback((loc: string) => {
    setLocation(loc);
  }, []);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
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
        <a href="/" style={{ color: "#666", textDecoration: "none", fontSize: 12 }}>
          postwriter.app
        </a>
      </header>

      {/* Reader */}
      <div style={{ flexGrow: 1, position: "relative" }}>
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
                "line-height": "1.8 !important",
                "padding": "0 0.5em !important",
              },
            });
          }}
        />
      </div>
    </div>
  );
}

export default Reader;
