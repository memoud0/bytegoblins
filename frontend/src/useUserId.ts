import { useCallback, useState } from "react";

export function useUserId() {
    const [userId, setUserIdState] = useState<string | null>(() =>
        localStorage.getItem("userId")
    );

    const persistUserId = useCallback(
        (next: string | null) => {
            if (next && next.trim()) {
                const normalized = next.trim().toLowerCase();
                localStorage.setItem("userId", normalized);
                setUserIdState(normalized);
            } else {
                localStorage.removeItem("userId");
                setUserIdState(null);
            }
        },
        [setUserIdState]
    );

    return { userId, setUserId: persistUserId };
}
