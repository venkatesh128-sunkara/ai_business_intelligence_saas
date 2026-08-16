declare module "react-plotly.js" {
  import * as React from "react";
  import { Figure } from "plotly.js";

  interface PlotParams {
    data: unknown[];
    layout?: Partial<Figure["layout"]>;
    frames?: unknown[];
    config?: Partial<Figure["config"]>;
    style?: React.CSSProperties;
    className?: string;
    id?: string;
    useResizeHandler?: boolean;
    onInitialized?: (...args: unknown[]) => void;
    onUpdate?: (...args: unknown[]) => void;
    onPurge?: (...args: unknown[]) => void;
    onError?: (...args: unknown[]) => void;
    onClick?: (...args: unknown[]) => void;
    onHover?: (...args: unknown[]) => void;
    onSelected?: (...args: unknown[]) => void;
    onRelayout?: (...args: unknown[]) => void;
    onLegendClick?: (...args: unknown[]) => void;
    onDoubleClick?: (...args: unknown[]) => void;
    onAfterPlot?: (...args: unknown[]) => void;
    divId?: string;
    revision?: number;
  }

  export default class PlotlyComponent extends React.Component<PlotParams> {}
}
