-- Pandoc filter for the HTML build of the guides (not used for the PDFs).
--   * figures: the sources say img/name.png (next to the source); the HTML page is one folder up,
--     so point at src/img/name.png, and give each figure a text description;
--   * tables: wrap them so a wide table scrolls sideways on a phone.
local alt = {
  ["loop.png"]          = "The ten steps of the daily loop: update develop, make a branch, work and commit, push, open a pull request, checks run, review, merge, live in about two minutes, clean up.",
  ["branches.png"]      = "The branches over time: a feature branch splits off develop and merges back through a pull request; later a release goes to master, is tagged v0.1.0, and master is merged back into develop.",
  ["note-path.png"]     = "Six steps from a written note to a live page: write, commit and push, open a pull request, the check runs, your lead reviews and gives an S-number, live in about two minutes.",
  ["note-steps.png"]    = "Six steps for creating a note: notebook, figures, page, index row, check, pull request and merge.",
  ["note-ai-steps.png"] = "Six steps for creating a note with an AI agent: you write the brief, the agent drafts, you verify the numbers, the agent wires up the index and changelog, you read the diff, then pull request and merge.",
  ["trace-pulse.png"]  = "Two traces drawn on the same scale. The top one is flat noise with a little jitter. The bottom one is flat until about sample 505, then jumps up sharply and slowly falls back: that is a pulse.",
  ["channels.png"]     = "A round detector divided into four sectors for channels 0 to 3. Channels 0, 1 and 3 hold a trace in this event and channel 2 reads all zeros. Channel 0 is outlined: it is the one this guide uses.",
}

function Image(el)
  if not FORMAT:match("html") then return nil end
  local name = el.src:match("^img/(.+)$")
  if name then
    el.src = "src/img/" .. name
    if #el.caption == 0 and alt[name] then
      el.caption = pandoc.Inlines({ pandoc.Str(alt[name]) })
    end
    return el
  end
end

function Table(el)
  if not FORMAT:match("html") then return nil end
  return pandoc.Div({ el }, pandoc.Attr("", { "table-scroll" }))
end
