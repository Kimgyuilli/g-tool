import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface NaverConnectModalProps {
  open: boolean;
  naverEmail: string;
  naverPassword: string;
  connecting: boolean;
  onEmailChange: (email: string) => void;
  onPasswordChange: (password: string) => void;
  onConnect: () => void;
  onClose: () => void;
}

export function NaverConnectModal({
  open,
  naverEmail,
  naverPassword,
  connecting,
  onEmailChange,
  onPasswordChange,
  onConnect,
  onClose,
}: NaverConnectModalProps) {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>네이버 메일 연결</DialogTitle>
          <DialogDescription>
            네이버 메일 설정에서 IMAP 사용 설정 후 앱 비밀번호를 생성하세요.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">네이버 이메일</label>
            <Input
              type="email"
              value={naverEmail}
              onChange={(e) => onEmailChange(e.target.value)}
              placeholder="example@naver.com"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">앱 비밀번호</label>
            <Input
              type="password"
              value={naverPassword}
              onChange={(e) => onPasswordChange(e.target.value)}
              placeholder="네이버 앱 비밀번호"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            취소
          </Button>
          <Button
            onClick={onConnect}
            disabled={connecting || !naverEmail || !naverPassword}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            {connecting ? "연결 중..." : "연결"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
