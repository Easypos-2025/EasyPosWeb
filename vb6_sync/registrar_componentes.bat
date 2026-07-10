@echo off
:: ============================================================
:: registrar_componentes.bat
:: Registra los componentes VB6 (DLL/OCX) con regsvr32 32-bit
:: Ejecutar como Administrador desde la carpeta donde esten los archivos
:: ============================================================

:: Verificar privilegios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ejecuta este archivo como Administrador.
    echo Clic derecho ^> "Ejecutar como administrador"
    pause
    exit /b 1
)

:: Usar regsvr32 de 32 bits (VB6 = componentes 32-bit)
set REG=%SystemRoot%\SysWOW64\regsvr32.exe
if not exist "%REG%" set REG=%SystemRoot%\System32\regsvr32.exe

set OK=0
set FAIL=0
set LOG=%~dp0registro_log.txt
echo Registro de componentes VB6 - %date% %time% > "%LOG%"
echo ============================================ >> "%LOG%"

call :registrar actskin4.ocx
call :registrar BarCode.dll
call :registrar comdlg32.ocx
call :registrar EASendMail.dll
call :registrar kiCryptoAPI.dll
call :registrar msadodc.ocx
call :registrar msbind.dll
call :registrar MSCOMCT2.OCX
call :registrar MSCOMM32.OCX
call :registrar MSDATGRD.OCX
call :registrar MSDATLST.OCX
call :registrar MSDBRPTR.DLL
call :registrar MSDE.DLL
call :registrar MSDERUN.DLL
call :registrar msflxgrd.ocx
call :registrar mshflxgd.ocx
call :registrar MSINET.OCX
call :registrar MSSTDFMT.DLL
call :registrar quricol32.dll
call :registrar scrrun.dll
call :registrar TABCTL32.OCX
call :registrar wmp.dll

echo.
echo ============================================
echo  Registro completado
echo  OK   : %OK%
echo  FALLO: %FAIL%
echo  Log  : %LOG%
echo ============================================
pause
exit /b 0


:registrar
set FILE=%~dp0%1
if not exist "%FILE%" (
    echo [ NO ENCONTRADO ] %1
    echo [ NO ENCONTRADO ] %1 >> "%LOG%"
    set /a FAIL+=1
    goto :eof
)
"%REG%" /s "%FILE%"
if %errorlevel% equ 0 (
    echo [ OK ] %1
    echo [ OK ] %1 >> "%LOG%"
    set /a OK+=1
) else (
    echo [ FALLO ] %1
    echo [ FALLO ] %1 >> "%LOG%"
    set /a FAIL+=1
)
goto :eof
