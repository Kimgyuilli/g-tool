import { useState, useCallback } from "react";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";
import type { UserInfo } from "@/features/auth/types";

interface UseNaverConnectProps {
  userId: number | null;
  setUserInfo: React.Dispatch<React.SetStateAction<UserInfo | null>>;
  loadCategoryCounts: () => Promise<void>;
}

export function useNaverConnect({
  userId,
  setUserInfo,
  loadCategoryCounts,
}: UseNaverConnectProps) {
  const [showNaverConnect, setShowNaverConnect] = useState(false);
  const [naverEmail, setNaverEmail] = useState("");
  const [naverPassword, setNaverPassword] = useState("");
  const [connectingNaver, setConnectingNaver] = useState(false);

  const handleConnectNaver = useCallback(async () => {
    if (!userId || !naverEmail || !naverPassword) return;
    setConnectingNaver(true);
    try {
      await apiFetch(`/api/naver/connect?user_id=${userId}`, {
        method: "POST",
        body: JSON.stringify({
          naver_email: naverEmail,
          naver_app_password: naverPassword,
        }),
      });
      toast.success("네이버 메일이 연결되었습니다.");
      setShowNaverConnect(false);
      setNaverEmail("");
      setNaverPassword("");
      const updatedInfo = await apiFetch<UserInfo>(`/auth/me?user_id=${userId}`);
      setUserInfo(updatedInfo);
      await loadCategoryCounts();
    } catch (err) {
      toast.error(`네이버 연결 실패: ${err}`);
    } finally {
      setConnectingNaver(false);
    }
  }, [userId, naverEmail, naverPassword, setUserInfo, loadCategoryCounts]);

  const closeNaverConnect = useCallback(() => {
    setShowNaverConnect(false);
    setNaverEmail("");
    setNaverPassword("");
  }, []);

  return {
    showNaverConnect,
    setShowNaverConnect,
    naverEmail,
    setNaverEmail,
    naverPassword,
    setNaverPassword,
    connectingNaver,
    handleConnectNaver,
    closeNaverConnect,
  };
}
