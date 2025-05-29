'use client';

import { useState } from 'react';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [mapUrl, setMapUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files?.[0];
    setFile(uploadedFile || null);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("엑셀 파일을 선택하세요.");
      return;
    }

    setLoading(true);
    setError(null);
    setMapUrl(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "지도 생성 실패");
      }

      setMapUrl(`http://localhost:5000${data.map_url}`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("알 수 없는 오류가 발생했습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50">
      <h1 className="text-3xl font-bold mb-6">📍 주소 지도 생성기</h1>

      <input
        type="file"
        accept=".xlsx, .xls"
        onChange={handleFileChange}
        className="mb-4"
      />

      <button
        onClick={handleUpload}
        disabled={loading}
        className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "처리 중..." : "지도 생성하기"}
      </button>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      {mapUrl && (
        <div className="mt-8 w-full max-w-4xl h-[600px]">
          <h2 className="text-xl font-semibold mb-2">🗺️ 결과 지도</h2>
          <iframe
            src={mapUrl}
            className="w-full h-full border"
            title="지도 결과"
          />
        </div>
      )}
    </main>
  );
}
