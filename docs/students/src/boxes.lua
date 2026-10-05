-- Turn fenced divs into coloured boxes: ::: tip / ::: careful / ::: checkpoint
local boxes = {
  tip        = {"Tip", "teal"},
  careful    = {"Careful", "red"},
  checkpoint = {"Checkpoint", "green"},
}
function Div(el)
  for cls, info in pairs(boxes) do
    if el.classes:includes(cls) then
      local out = {}
      table.insert(out, pandoc.RawBlock("latex",
        "\\begin{tcolorbox}[colback=" .. info[2] .. "!5!white,colframe=" .. info[2] ..
        "!70!black,title={\\bfseries " .. info[1] .. "},boxrule=0.8pt,arc=3pt,left=8pt,right=8pt,top=6pt,bottom=6pt,breakable]"))
      for _, b in ipairs(el.content) do table.insert(out, b) end
      table.insert(out, pandoc.RawBlock("latex", "\\end{tcolorbox}"))
      return out
    end
  end
end
