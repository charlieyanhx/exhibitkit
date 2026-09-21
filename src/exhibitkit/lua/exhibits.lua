-- exhibitkit pandoc filter.
-- Maps the document's structural devices to the LaTeX environments defined in templates/preamble.tex:
--   Div.exhibit  -> \begin{exhibit}[short]{title}\label{id}  (short = `short` attr, else the title before its first colon) ... \exnote{} \exsource{} \end{exhibit}   (tables become booktabs tabulars)
--   Div.box      -> inthischapter panel;  Div.callout -> keybox;  Div.warning -> warnbox
--   Header 1/2/3 -> \partopen / \chapterhead{n}{title} / \subhead   (in appendix mode, H2 -> \subhead)
--   Div.pullquote / .aside / .keynumber{value=} -> margin-column devices;  Div.closing -> closing box
--   Link #ex-... -> "Exhibit~\ref"   ([](#ex-x) -> Exhibit N;  [text](#ex-x) -> text (Exhibit N))
-- Attribute strings (title, source, note) are themselves Markdown and are rendered through pandoc.

local mode = 'body'
local layout = 'primer'

local function md2tex(s)
  if s == nil or s == '' then return '' end
  local doc = pandoc.read(s, 'markdown+smart')
  local out = pandoc.write(doc, 'latex')
  return (out:gsub('\n+$', ''))
end

local function inlines2tex(inl)
  local out = pandoc.write(pandoc.Pandoc({pandoc.Plain(inl)}), 'latex')
  return (out:gsub('\n+$', ''))
end

local function raw(s) return pandoc.RawBlock('latex', s) end

local function cell_tex(cell)
  local out = pandoc.write(pandoc.Pandoc(cell.contents), 'latex')
  return (out:gsub('\n+$', ''))
end

local function table_to_tabular(tbl, cols)
  local aligns = {}
  for _, cs in ipairs(tbl.colspecs) do
    local a = cs[1]
    aligns[#aligns + 1] = (a == 'AlignRight') and 'r' or ((a == 'AlignCenter') and 'c' or 'l')
  end
  local spec = cols or table.concat(aligns)
  local lines = { '\\begin{extabular}{' .. spec .. '}\\toprule' }
  local function row_tex(row, bold)
    local cells = {}
    for _, c in ipairs(row.cells) do
      local t = cell_tex(c)
      if bold and t ~= '' then t = '\\textbf{' .. t .. '}' end
      cells[#cells + 1] = t
    end
    return table.concat(cells, ' & ') .. ' \\\\'
  end
  for _, row in ipairs(tbl.head.rows) do lines[#lines + 1] = row_tex(row, true) end
  if #tbl.head.rows > 0 then lines[#lines + 1] = '\\midrule' end
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do lines[#lines + 1] = row_tex(row, false) end
  end
  lines[#lines + 1] = '\\bottomrule\\end{extabular}'
  return raw(table.concat(lines, '\n'))
end

local function exhibit(el)
  local a = el.attributes
  local id = el.identifier
  local env = (a.float == 'false') and 'exhibitfixed' or 'exhibit'
  if layout == 'issue' then env = (a.wide == 'true') and 'exhibitfixed' or 'exhibitcol' end
  local width = a.width or '100%'
  if width:match('^[%d%.]+$') then width = tostring(math.floor(tonumber(width) * 100 + 0.5)) .. '%' end
  local short = a.short or (a.title or ''):match('^(.-):') or ''
  local out = { raw('\\begin{' .. env .. '}[' .. md2tex(short) .. ']{' .. md2tex(a.title) .. '}\\label{' .. id .. '}') }
  if a.subtitle and a.subtitle ~= '' then out[#out + 1] = raw('\\exsubtitle{' .. md2tex(a.subtitle) .. '}') end
  for _, b in ipairs(el.content) do
    if b.t == 'Table' then
      out[#out + 1] = table_to_tabular(b, a.cols)
    else
      b = pandoc.walk_block(b, { Image = function(img)
        if not img.attributes.width and not img.attributes.height then img.attributes.width = width end
        return img
      end })
      out[#out + 1] = b
    end
  end
  if a.note and a.note ~= '' then out[#out + 1] = raw('\\exnote{' .. md2tex(a.note) .. '}') end
  out[#out + 1] = raw('\\exsource{' .. md2tex(a.source or '') .. '}')
  out[#out + 1] = raw('\\end{' .. env .. '}')
  return out
end

local function blocks2tex(blocks)
  local out = pandoc.write(pandoc.Pandoc(blocks), 'latex')
  return (out:gsub('\n+$', ''))
end

local function boxed(el, env, default_title)
  local title = el.attributes.title or default_title
  local out = { raw('\\begin{' .. env .. '}{' .. md2tex(title) .. '}') }
  for _, b in ipairs(el.content) do out[#out + 1] = b end
  out[#out + 1] = raw('\\end{' .. env .. '}')
  return out
end

local function Div(el)
  if el.classes:includes('exhibit') then return exhibit(el) end
  if el.classes:includes('box') then return boxed(el, 'inthischapter', 'In this chapter') end
  if el.classes:includes('callout') then return boxed(el, 'keybox', '') end
  if el.classes:includes('warning') then
    local out = { raw('\\begin{warnbox}') }
    for _, b in ipairs(el.content) do out[#out + 1] = b end
    out[#out + 1] = raw('\\end{warnbox}')
    return out
  end
  if el.classes:includes('pullquote') then return raw('\\pullquote{' .. blocks2tex(el.content) .. '}') end
  if el.classes:includes('colbreak') then return raw('\\columnbreak') end
  if el.classes:includes('small') or el.classes:includes('fineprint') then
    local size = el.classes:includes('small') and '\\footnotesize' or '\\scriptsize\\color{slate}'
    local out = { raw('\\begingroup' .. size) }
    for _, b in ipairs(el.content) do out[#out + 1] = b end
    out[#out + 1] = raw('\\par\\endgroup')
    return out
  end
  if el.classes:includes('deck') then return raw('\\issuedeck{' .. blocks2tex(el.content) .. '}') end
  if el.classes:includes('claim') then
    -- a falsifiable claim: the sentence, with its id and the date it resolves set as a small label beside it
    local a = el.attributes
    local label = 'Claim ' .. (a.id or el.identifier or '')
    if a.resolve and a.resolve ~= '' then label = label .. ' \\textperiodcentered{} resolves ' .. a.resolve end
    return raw('\\claimblock{' .. md2tex(label) .. '}{' .. blocks2tex(el.content) .. '}')
  end
  if el.classes:includes('keynumber') and layout == 'issue' then
    return raw('\\keynumbercol{' .. md2tex(el.attributes.value or '') .. '}{' .. blocks2tex(el.content) .. '}')
  end
  if el.classes:includes('aside') then return raw('\\aside{' .. blocks2tex(el.content) .. '}') end
  if el.classes:includes('keynumber') then
    return raw('\\keynumber{' .. md2tex(el.attributes.value or '') .. '}{' .. blocks2tex(el.content) .. '}')
  end
  if el.classes:includes('closing') then
    local out = { raw('\\begin{closingbox}') }
    for _, b in ipairs(el.content) do out[#out + 1] = b end
    out[#out + 1] = raw('\\end{closingbox}')
    return out
  end
  return nil
end

local function Header(el)
  local txt = inlines2tex(el.content)
  if el.level == 1 then
    local part, rest = txt:match('^(Part%s+%S+)%s*%-%-%-?%s*(.*)$')
    if not part then part, rest = txt:match('^([^:]+):%s*(.*)$') end
    if part then return raw('\\partopen{' .. part .. '}{' .. rest .. '}') end
    return raw('\\partopen{' .. txt .. '}{}')
  elseif el.level == 2 then
    if mode == 'appendix' then return raw('\\subhead{' .. txt .. '}') end
    if layout == 'issue' then return raw('\\issuesection{' .. txt .. '}{}') end
    local num, rest = txt:match('^(%d+)%.%s*(.*)$')
    if num then return raw('\\chapterhead{' .. num .. '}{' .. rest .. '}') end
    return raw('\\chapterhead{}{' .. txt .. '}')
  elseif el.level == 3 then
    return raw('\\subhead{' .. txt .. '}')
  elseif el.level == 4 and layout == 'issue' then
    return raw('\\caplabel{' .. txt .. '}')
  elseif el.level >= 4 then
    return pandoc.Para({ pandoc.Strong(el.content) })
  end
end

local function Link(el)
  if el.target:sub(1, 4) == '#ex-' then
    local id = el.target:sub(2)
    local ref = pandoc.RawInline('latex', '\\hyperref[' .. id .. ']{Exhibit~\\ref*{' .. id .. '}}')
    if #el.content == 0 then return ref end
    local out = {}
    for _, x in ipairs(el.content) do out[#out + 1] = x end
    out[#out + 1] = pandoc.Str(' (')
    out[#out + 1] = ref
    out[#out + 1] = pandoc.Str(')')
    return out
  end
  return nil
end

local function is_raw(b, prefix)
  return b.t == 'RawBlock' and b.format == 'latex' and b.text:sub(1, #prefix) == prefix
end

local function issue_columns(doc)
  -- After Div/Header mapping: split at \issuesection heads; fold a following \issuedeck into the head;
  -- wrap the rest in multicols, breaking out around wide (exhibitfixed) exhibits.
  local out, cur, open = {}, nil, false
  local function close() if open then out[#out + 1] = raw('\\end{multicols}') open = false end end
  local firstpending = false
  local function ensure_open(first)
    if open then return end
    -- a column exhibit opening the columns cannot break before itself: measure it at column width, ask for that much
    -- room, and only then start the columns (\exhibitcolfirstend emits the \begin{multicols})
    if first and is_raw(first, '\\begin{exhibitcol}') then
      first.text = first.text:gsub('^\\begin{exhibitcol}', '\\exhibitcolfirstbegin', 1); firstpending = true
    else
      out[#out + 1] = raw('\\begin{multicols}{2}')
    end
    open = true
  end
  local i = 1
  while i <= #doc.blocks do
    local b = doc.blocks[i]
    if is_raw(b, '\\issuesection{') then
      close()
      local head = b.text
      local nxt = doc.blocks[i + 1]
      if nxt and is_raw(nxt, '\\issuedeck{') then
        head = head:sub(1, -2) .. nxt.text:sub(#'\\issuedeck{' + 1)  -- replace the trailing {} with {deck}
        i = i + 1
      end
      out[#out + 1] = raw(head)
    elseif is_raw(b, '\\begin{exhibitfixed}') then
      close(); out[#out + 1] = b
    elseif is_raw(b, '\\end{exhibitfixed}') then
      out[#out + 1] = b
    elseif b.t == 'RawBlock' and b.format == 'latex' and (b.text == '\\end{multicols}' or b.text == '\\begin{multicols}{2}') then
      out[#out + 1] = b
    else
      -- blocks that belong to a wide exhibit (between its begin and end) pass through unchanged
      local inwide = false
      for k = #out, 1, -1 do
        if is_raw(out[k], '\\end{exhibitfixed}') then break end
        if is_raw(out[k], '\\begin{exhibitfixed}') then inwide = true break end
      end
      if not inwide then ensure_open(b) end
      if firstpending and is_raw(b, '\\end{exhibitcol}') then b = raw('\\exhibitcolfirstend'); firstpending = false end
      out[#out + 1] = b
    end
    i = i + 1
  end
  close()
  doc.blocks = out
  return doc
end

return {
  { Meta = function(m)
      if m.mode then mode = pandoc.utils.stringify(m.mode) end
      if m.layout then layout = pandoc.utils.stringify(m.layout) end
      return m
    end },
  { Div = Div, Header = Header, Link = Link, HorizontalRule = function() return {} end },
  { Pandoc = function(doc) if layout == 'issue' and mode == 'body' then return issue_columns(doc) end return doc end },
}
