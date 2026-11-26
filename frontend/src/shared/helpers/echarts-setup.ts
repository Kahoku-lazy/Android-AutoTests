import * as echarts from "echarts/core"
import { BarChart, LineChart, PieChart } from "echarts/charts"
import {
  AxisPointerComponent,
  GraphicComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components"
import { CanvasRenderer } from "echarts/renderers"

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  AxisPointerComponent,
  GraphicComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
])

export default echarts
