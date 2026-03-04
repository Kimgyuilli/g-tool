"use client";

import { useMemo } from "react";
import DOMPurify from "dompurify";

interface HtmlEmailRendererProps {
  html: string;
}

export function HtmlEmailRenderer({ html }: HtmlEmailRendererProps) {
  const sanitizedHtml = useMemo(() => {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [
        "a", "abbr", "address", "b", "blockquote", "br", "caption",
        "cite", "code", "col", "colgroup", "dd", "del", "details",
        "dfn", "div", "dl", "dt", "em", "figcaption", "figure",
        "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img",
        "ins", "kbd", "li", "mark", "ol", "p", "pre", "q", "s",
        "samp", "section", "small", "span", "strong", "sub",
        "summary", "sup", "table", "tbody", "td", "tfoot", "th",
        "thead", "tr", "u", "ul", "var", "wbr", "center", "font",
      ],
      ALLOWED_ATTR: [
        "href", "src", "alt", "title", "width", "height",
        "style", "class", "id", "target", "rel",
        "colspan", "rowspan", "cellpadding", "cellspacing",
        "border", "align", "valign", "bgcolor", "color",
        "face", "size",
      ],
      ALLOW_DATA_ATTR: false,
      ADD_ATTR: ["target"],
    });
  }, [html]);

  return (
    <div
      className="prose prose-sm dark:prose-invert max-w-none break-words"
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
}
