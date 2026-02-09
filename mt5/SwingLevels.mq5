//+------------------------------------------------------------------+
//|                                                  SwingLevels.mq5 |
//|                         Swing High/Low Horizontal Level Indicator |
//|                         Draws clean S/R lines for AI analysis     |
//+------------------------------------------------------------------+
#property copyright "GBPJPY AI Trade Analyst Bot"
#property link      ""
#property version   "1.10"
#property indicator_chart_window
#property indicator_plots   0
#property indicator_buffers 0

//--- Input parameters
input int      InpLookback     = 3;             // Swing Lookback (bars each side)
input int      InpMaxLines     = 15;            // Max Lines on Chart
input color    InpHighColor    = clrRed;        // Swing High Line Color
input color    InpLowColor     = clrDodgerBlue; // Swing Low Line Color
input int      InpLabelSize    = 7;             // Price Label Font Size
input bool     InpRemoveBroken = true;          // Remove Broken Levels

//--- Prefix for all objects created by this indicator
string g_prefix = "SWL_";
int    g_lastBars = 0;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                          |
//+------------------------------------------------------------------+
int OnInit()
{
   g_lastBars = 0;
   Print("SwingLevels v1.10 initialized (lookback=", InpLookback,
         ", max=", InpMaxLines, ")");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, g_prefix);
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                                |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   //--- Need enough bars for swing detection
   if(rates_total < InpLookback * 2 + 1)
      return rates_total;

   //--- Only recalculate on new bar or first run
   if(rates_total == g_lastBars)
      return rates_total;
   g_lastBars = rates_total;

   //--- Set arrays as series (index 0 = newest bar)
   ArraySetAsSeries(time, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

   //--- Remove old objects
   ObjectsDeleteAll(0, g_prefix);

   //--- Find swing highs and lows
   //--- Store as: price, time, type ("H" or "L")
   //--- Scan from recent to old, collect up to a reasonable number
   int maxScan = MathMin(rates_total - InpLookback, 500);  // Don't scan entire history
   double   prices[];
   datetime times[];
   int      types[];  // 1 = swing high, -1 = swing low

   ArrayResize(prices, 0);
   ArrayResize(times, 0);
   ArrayResize(types, 0);

   double currentClose = close[0];

   for(int i = InpLookback; i < maxScan; i++)
   {
      //--- Check swing high
      bool isHigh = true;
      for(int j = 1; j <= InpLookback; j++)
      {
         if(high[i - j] >= high[i] || high[i + j] >= high[i])
         {
            isHigh = false;
            break;
         }
      }

      if(isHigh)
      {
         //--- Skip broken levels (price closed above this high)
         if(InpRemoveBroken && currentClose > high[i])
         {
            // Level broken, skip
         }
         else
         {
            int sz = ArraySize(prices);
            ArrayResize(prices, sz + 1);
            ArrayResize(times, sz + 1);
            ArrayResize(types, sz + 1);
            prices[sz] = high[i];
            times[sz]  = time[i];
            types[sz]  = 1;
         }
      }

      //--- Check swing low
      bool isLow = true;
      for(int j = 1; j <= InpLookback; j++)
      {
         if(low[i - j] <= low[i] || low[i + j] <= low[i])
         {
            isLow = false;
            break;
         }
      }

      if(isLow)
      {
         //--- Skip broken levels (price closed below this low)
         if(InpRemoveBroken && currentClose < low[i])
         {
            // Level broken, skip
         }
         else
         {
            int sz = ArraySize(prices);
            ArrayResize(prices, sz + 1);
            ArrayResize(times, sz + 1);
            ArrayResize(types, sz + 1);
            prices[sz] = low[i];
            times[sz]  = time[i];
            types[sz]  = -1;
         }
      }
   }

   //--- Limit to InpMaxLines (array is already ordered most-recent-first)
   int total = ArraySize(prices);
   int drawCount = MathMin(total, InpMaxLines);

   if(drawCount == 0)
   {
      Print("SwingLevels: No levels found (scanned ", maxScan, " bars)");
      return rates_total;
   }

   //--- Draw lines
   for(int i = 0; i < drawCount; i++)
   {
      color    clr  = (types[i] == 1) ? InpHighColor : InpLowColor;
      string   tag  = (types[i] == 1) ? "H" : "L";
      string   name = g_prefix + tag + IntegerToString(i);

      //--- Horizontal line at swing price
      ObjectCreate(0, name, OBJ_HLINE, 0, 0, prices[i]);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);

      //--- Small price label
      string lblName = g_prefix + "T" + IntegerToString(i);
      ObjectCreate(0, lblName, OBJ_TEXT, 0, time[0], prices[i]);
      ObjectSetString(0, lblName, OBJPROP_TEXT, DoubleToString(prices[i], 3));
      ObjectSetString(0, lblName, OBJPROP_FONT, "Arial");
      ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, InpLabelSize);
      ObjectSetInteger(0, lblName, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, lblName, OBJPROP_HIDDEN, true);
   }

   ChartRedraw(0);

   if(prev_calculated == 0)
      Print("SwingLevels: Drew ", drawCount, " levels (", total, " found, max ", InpMaxLines, ")");

   return rates_total;
}
//+------------------------------------------------------------------+
