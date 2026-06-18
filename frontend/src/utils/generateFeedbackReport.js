import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import docmindLogo from '../assets/docmind_logo_dark.png'

const BRAND = { primary: [13, 110, 115], dark: [15, 28, 29], muted: [138, 163, 165] }

async function loadLogoDataUrl(url) {
  try {
    const res = await fetch(url)
    if (!res.ok) return null
    const blob = await res.blob()
    return await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  } catch {
    return null
  }
}

function drawHeader(doc, title, subtitle, logoDataUrl) {
  const pageW = doc.internal.pageSize.getWidth()
  const titleMaxW = logoDataUrl ? pageW - 14 - 18 - 24 : pageW - 28

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(20)
  const titleLines = doc.splitTextToSize(title, titleMaxW)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  const subtitleLines = doc.splitTextToSize(subtitle, titleMaxW)

  const titleBlockH = Math.max(titleLines.length, 1) * 9
  const subtitleY = 22 + titleBlockH + 2
  const subtitleBlockH = subtitleLines.length * 5 + 4
  const headerH = Math.max(44, subtitleY + subtitleBlockH)

  doc.setFillColor(...BRAND.dark)
  doc.rect(0, 0, pageW, headerH, 'F')

  doc.setFillColor(...BRAND.primary)
  doc.rect(0, headerH, pageW, 3, 'F')

  if (logoDataUrl) {
    const logoH = 18
    const logoW = 18
    const logoX = pageW - 14 - logoW
    const logoY = (headerH - logoH) / 2
    doc.addImage(logoDataUrl, 'PNG', logoX, logoY, logoW, logoH)
  }

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(20)
  doc.setTextColor(255, 255, 255)
  doc.text(titleLines, 14, 22)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(...BRAND.muted)
  doc.text(subtitleLines, 14, subtitleY)

  return headerH + 3
}

function drawSummaryBox(doc, y, stats) {
  const w = doc.internal.pageSize.getWidth() - 28
  doc.setFillColor(240, 245, 245)
  doc.roundedRect(14, y, w, 32, 3, 3, 'F')

  const cols = [
    { label: 'Total Entries', value: stats.total },
    { label: 'Positive', value: stats.positive, color: [34, 197, 94] },
    { label: 'Negative', value: stats.negative, color: [239, 68, 68] },
    { label: 'Satisfaction', value: `${stats.satisfaction}%`, color: BRAND.primary },
  ]

  const colW = w / cols.length
  cols.forEach((col, i) => {
    const x = 14 + colW * i + colW / 2

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(16)
    doc.setTextColor(...(col.color || [30, 30, 30]))
    doc.text(String(col.value), x, y + 14, { align: 'center' })

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(100, 100, 100)
    doc.text(col.label, x, y + 23, { align: 'center' })
  })

  return y + 38
}

function drawSubjectBreakdown(doc, y, subjectMap) {
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(12)
  doc.setTextColor(30, 30, 30)
  doc.text('Feedback Breakdown by Subject', 14, y)
  y += 6

  const rows = Object.entries(subjectMap).map(([name, data]) => {
    const sat = data.up + data.down > 0
      ? Math.round((data.up / (data.up + data.down)) * 100)
      : 0
    return [name, String(data.up + data.down), String(data.up), String(data.down), `${sat}%`]
  })

  autoTable(doc, {
    startY: y,
    head: [['Subject', 'Total', 'Positive', 'Negative', 'Satisfaction']],
    body: rows,
    theme: 'grid',
    headStyles: { fillColor: BRAND.primary, fontSize: 9, fontStyle: 'bold' },
    bodyStyles: { fontSize: 9 },
    alternateRowStyles: { fillColor: [245, 250, 250] },
    margin: { left: 14, right: 14 },
    columnStyles: {
      0: { cellWidth: 'auto' },
      1: { halign: 'center', cellWidth: 28 },
      2: { halign: 'center', cellWidth: 28, textColor: [34, 197, 94] },
      3: { halign: 'center', cellWidth: 28, textColor: [239, 68, 68] },
      4: { halign: 'center', cellWidth: 30 },
    },
  })

  return doc.lastAutoTable.finalY + 10
}

function drawNegativeFeedbackDetails(doc, y, negativeFeedback) {
  if (negativeFeedback.length === 0) return y

  if (y > doc.internal.pageSize.getHeight() - 80) {
    doc.addPage()
    y = 20
  }

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(12)
  doc.setTextColor(239, 68, 68)
  doc.text('Negative Feedback — Action Items', 14, y)
  y += 3

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(100, 100, 100)
  doc.text('These entries received negative feedback and may need developer review.', 14, y + 5)
  y += 10

  const rows = negativeFeedback.map((f) => [
    f.subject,
    f.student,
    f.question,
    f.aiResponse.length > 120 ? f.aiResponse.slice(0, 120) + '…' : f.aiResponse,
    f.timestamp,
  ])

  autoTable(doc, {
    startY: y,
    head: [['Subject', 'Student', 'Question', 'AI Response', 'Date']],
    body: rows,
    theme: 'grid',
    headStyles: { fillColor: [180, 40, 40], fontSize: 8, fontStyle: 'bold' },
    bodyStyles: { fontSize: 7, cellPadding: 3 },
    alternateRowStyles: { fillColor: [255, 245, 245] },
    margin: { left: 14, right: 14 },
    columnStyles: {
      0: { cellWidth: 32 },
      1: { cellWidth: 28 },
      2: { cellWidth: 50 },
      3: { cellWidth: 'auto' },
      4: { cellWidth: 28 },
    },
  })

  return doc.lastAutoTable.finalY + 10
}

function drawAllFeedbackTable(doc, y, feedbackList) {
  if (y > doc.internal.pageSize.getHeight() - 60) {
    doc.addPage()
    y = 20
  }

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(12)
  doc.setTextColor(30, 30, 30)
  doc.text('Complete Feedback Log', 14, y)
  y += 6

  const rows = feedbackList.map((f) => [
    f.subject,
    f.student,
    f.question,
    f.aiResponse.length > 100 ? f.aiResponse.slice(0, 100) + '…' : f.aiResponse,
    f.feedback === 'up' ? 'Positive' : 'Negative',
    f.timestamp,
  ])

  autoTable(doc, {
    startY: y,
    head: [['Subject', 'Student', 'Question', 'AI Response', 'Sentiment', 'Date']],
    body: rows,
    theme: 'grid',
    headStyles: { fillColor: BRAND.primary, fontSize: 8, fontStyle: 'bold' },
    bodyStyles: { fontSize: 7, cellPadding: 3 },
    alternateRowStyles: { fillColor: [245, 250, 250] },
    margin: { left: 14, right: 14 },
    columnStyles: {
      0: { cellWidth: 28 },
      1: { cellWidth: 24 },
      2: { cellWidth: 42 },
      3: { cellWidth: 'auto' },
      4: { cellWidth: 22, halign: 'center' },
      5: { cellWidth: 26 },
    },
    didParseCell(data) {
      if (data.section === 'body' && data.column.index === 4) {
        data.cell.styles.textColor = data.cell.raw === 'Positive' ? [34, 197, 94] : [239, 68, 68]
        data.cell.styles.fontStyle = 'bold'
      }
    },
  })

  return doc.lastAutoTable.finalY + 10
}

function drawFooter(doc) {
  const pages = doc.internal.getNumberOfPages()
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i)
    const h = doc.internal.pageSize.getHeight()
    doc.setFontSize(7)
    doc.setTextColor(...BRAND.muted)
    doc.text(`DocMind — Confidential`, 14, h - 8)
    doc.text(`Page ${i} of ${pages}`, doc.internal.pageSize.getWidth() - 14, h - 8, { align: 'right' })
  }
}

export async function generateFeedbackReport(feedbackList, subjectStats, filters = {}) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })

  const filterParts = []
  if (filters.semester) filterParts.push(`Semester: ${filters.semester}`)
  if (filters.subject) filterParts.push(`Subject: ${filters.subject}`)
  if (filters.sentiment && filters.sentiment !== 'all') filterParts.push(`Sentiment: ${filters.sentiment}`)
  const subtitle = [
    `Generated on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`,
    filterParts.length ? `Filters — ${filterParts.join(' | ')}` : 'All data (unfiltered)',
  ].join('  •  ')

  const logoDataUrl = await loadLogoDataUrl(docmindLogo)
  const contentStartY = drawHeader(doc, 'DocMind — Tutor Bot Feedback Report', subtitle, logoDataUrl)

  const positive = feedbackList.filter((f) => f.feedback === 'up').length
  const negative = feedbackList.filter((f) => f.feedback === 'down').length
  const total = feedbackList.length
  const satisfaction = total > 0 ? Math.round((positive / total) * 100) : 0

  let y = drawSummaryBox(doc, contentStartY + 6, { total, positive, negative, satisfaction })

  const subjectMap = {}
  feedbackList.forEach((f) => {
    if (!subjectMap[f.subject]) subjectMap[f.subject] = { up: 0, down: 0 }
    subjectMap[f.subject][f.feedback === 'up' ? 'up' : 'down']++
  })

  y = drawSubjectBreakdown(doc, y, subjectMap)

  const negativeFeedback = feedbackList.filter((f) => f.feedback === 'down')
  y = drawNegativeFeedbackDetails(doc, y, negativeFeedback)
  drawAllFeedbackTable(doc, y, feedbackList)

  drawFooter(doc)

  const timestamp = new Date().toISOString().slice(0, 10)
  doc.save(`docmind-feedback-report-${timestamp}.pdf`)
}
