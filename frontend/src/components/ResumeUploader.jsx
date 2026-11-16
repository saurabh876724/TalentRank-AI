import { useRef, useState } from 'react'
import { UploadCloud, FileText, X, CheckCircle2, AlertCircle } from 'lucide-react'
import { uploadResumes, getApiError } from '../services/api'
import { useApp } from '../context/AppContext'
import { MAX_FILE_SIZE, MAX_BATCH, ALLOWED_EXTENSIONS } from '../utils/format'
import LoadingSpinner from './LoadingSpinner'

function validateFile(file) {
  const lower = file.name.toLowerCase()
  if (!ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
    return 'Unsupported type — only PDF and DOCX are accepted.'
  }
  if (file.size === 0) return 'File is empty (0 bytes).'
  if (file.size > MAX_FILE_SIZE) return 'Exceeds the 5 MB size limit.'
  return null
}

export default function ResumeUploader() {
  const { setUploadedCandidates, setUploadErrors, uploadedCandidates, uploadErrors } = useApp()
  const [staged, setStaged] = useState([])
  const [rejected, setRejected] = useState([])
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [serverError, setServerError] = useState(null)
  const [lastSummary, setLastSummary] = useState(null)
  const inputRef = useRef(null)

  const addFiles = (fileList) => {
    const incoming = Array.from(fileList)
    const accepted = []
    const refused = []
    for (const file of incoming) {
      const problem = validateFile(file)
      if (problem) refused.push({ name: file.name, reason: problem })
      else if (!staged.some((f) => f.name === file.name && f.size === file.size)) accepted.push(file)
    }
    const combined = [...staged, ...accepted]
    if (combined.length > MAX_BATCH) {
      refused.push({
        name: `${combined.length - MAX_BATCH} file(s)`,
        reason: `Batch limit is ${MAX_BATCH} files.`,
      })
      setStaged(combined.slice(0, MAX_BATCH))
    } else {
      setStaged(combined)
    }
    setRejected(refused)
  }

  const onDrop = (event) => {
    event.preventDefault()
    setDragOver(false)
    if (event.dataTransfer?.files?.length) addFiles(event.dataTransfer.files)
  }

  const removeStaged = (index) => setStaged(staged.filter((_, i) => i !== index))

  const handleUpload = async () => {
    if (!staged.length || uploading) return
    setUploading(true)
    setProgress(0)
    setServerError(null)
    try {
      const result = await uploadResumes(staged, (event) => {
        if (event.total) setProgress(Math.round((event.loaded / event.total) * 100))
      })
      setUploadedCandidates((prev) => {
        const existingIds = new Set(prev.map((c) => c.id))
        return [...prev, ...result.candidates.filter((c) => !existingIds.has(c.id))]
      })
      setUploadErrors(result.errors || [])
      setLastSummary({
        total: result.total_uploaded,
        success: result.successfully_processed,
        failed: result.failed,
      })
      setStaged([])
      setRejected([])
    } catch (error) {
      setServerError(getApiError(error))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragOver ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-slate-50 hover:border-indigo-400'
        }`}
        aria-label="Drop resumes here or click to browse"
      >
        <UploadCloud className="h-10 w-10 text-indigo-500" />
        <p className="mt-3 text-sm font-semibold text-slate-700">
          Drag & drop resumes here, or click to browse
        </p>
        <p className="mt-1 text-xs text-slate-400">
          PDF or DOCX · up to {MAX_BATCH} files · max 5 MB each
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx"
          className="hidden"
          data-testid="resume-file-input"
          onChange={(e) => {
            addFiles(e.target.files)
            e.target.value = ''
          }}
        />
      </div>

      {rejected.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          {rejected.map((r, i) => (
            <p key={i}>
              <strong>{r.name}</strong>: {r.reason}
            </p>
          ))}
        </div>
      )}

      {staged.length > 0 && (
        <div className="card divide-y divide-slate-100">
          {staged.map((file, index) => (
            <div key={`${file.name}-${index}`} className="flex items-center justify-between px-4 py-2.5">
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <FileText className="h-4 w-4 text-slate-400" />
                <span className="truncate">{file.name}</span>
                <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(0)} KB</span>
              </div>
              <button onClick={() => removeStaged(index)} aria-label={`Remove ${file.name}`}>
                <X className="h-4 w-4 text-slate-400 hover:text-rose-500" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button className="btn-primary" onClick={handleUpload} disabled={!staged.length || uploading}>
          {uploading ? 'Uploading…' : `Upload ${staged.length || ''} resume${staged.length === 1 ? '' : 's'}`}
        </button>
        {uploading && (
          <div className="flex flex-1 items-center gap-2">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
              <div className="h-full bg-indigo-600 transition-all" style={{ width: `${progress}%` }} />
            </div>
            <span className="text-xs text-slate-500">{progress}%</span>
          </div>
        )}
      </div>

      {uploading && progress === 100 && <LoadingSpinner label="Processing resumes on the server…" />}
      {serverError && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {serverError}
        </div>
      )}

      {lastSummary && (
        <div className="flex flex-wrap gap-3 text-sm">
          <span className="badge bg-slate-100 text-slate-700">Uploaded: {lastSummary.total}</span>
          <span className="badge bg-emerald-50 text-emerald-700">
            <CheckCircle2 className="mr-1 h-3.5 w-3.5" /> Processed: {lastSummary.success}
          </span>
          <span className="badge bg-rose-50 text-rose-700">Failed: {lastSummary.failed}</span>
        </div>
      )}

      {uploadErrors.length > 0 && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <p className="mb-1 font-semibold">Failed files</p>
          {uploadErrors.map((e, i) => (
            <p key={i}>
              <strong>{e.filename}</strong>: {e.error}
            </p>
          ))}
        </div>
      )}

      {uploadedCandidates.length > 0 && (
        <p className="text-sm text-slate-500">
          <strong className="text-slate-700">{uploadedCandidates.length}</strong> processed candidate
          {uploadedCandidates.length === 1 ? '' : 's'} ready for analysis.
        </p>
      )}
    </div>
  )
}