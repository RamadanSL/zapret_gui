@echo off
chcp 65001 > nul

:: Запрашиваем комментарий к коммиту
set /p commit_message="Введите описание коммита: "

:: Если комментарий пустой, используем стандартный
if "%commit_message%"=="" (
    set "commit_message=Update"
)

echo.
echo ===================================
echo.

:: Добавляем все измененные и новые файлы
git add .
echo "git add ." - выполнено.
echo.

:: Делаем коммит с вашим сообщением
git commit -m "%commit_message%"
echo "git commit" - выполнено.
echo.

:: Отправляем изменения в удаленный репозиторий
git push origin main
echo.
echo "git push" - выполнено.
echo.

echo ===================================
echo.
echo Готово! Изменения отправлены на GitHub.
echo.

pause 